use serde::Serialize;
use serde_json::Value;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Manager, State};

const BRIDGE_FILE: &str = "silabs-humanizer-bridge.exe";
const MODEL_FILE: &str = "qwen3-1.7b.gguf";

fn bundle_resource_dir(app: &AppHandle) -> Result<PathBuf, String> {
    app.path()
        .resource_dir()
        .map_err(|err| format!("Cannot locate offline application resources: {err}"))
}

fn bundled_model_path(app: &AppHandle) -> Result<PathBuf, String> {
    Ok(bundle_resource_dir(app)?.join("model").join(MODEL_FILE))
}

#[derive(Serialize)]
struct RuntimeInfo {
    packaged: bool,
    model_path: Option<String>,
}

#[tauri::command]
fn runtime_info(app: AppHandle) -> RuntimeInfo {
    let model_path = if cfg!(debug_assertions) {
        None
    } else {
        bundled_model_path(&app).ok().filter(|path| path.is_file())
            .map(|path| path.to_string_lossy().into_owned())
    };
    RuntimeInfo {
        packaged: !cfg!(debug_assertions),
        model_path,
    }
}

struct BridgeProcess {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
}

impl BridgeProcess {
    fn start(app: &AppHandle) -> Result<Self, String> {
        let mut command = if cfg!(debug_assertions) {
            // Development: reuse repository Python. No network is needed.
            let python = std::env::var("SILABS_HUMANIZER_PYTHON")
                .unwrap_or_else(|_| "python".to_owned());
            let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../../..")
                .canonicalize()
                .map_err(|err| format!("Cannot locate Silabs AI repository: {err}"))?;
            let mut process = Command::new(python);
            process
                .arg("-u")
                .arg("-m")
                .arg("products.humanizer.service.desktop_bridge")
                .current_dir(&root)
                .env("PYTHONPATH", &root)
                .env("PYTHONUTF8", "1")
                .env("PYTHONIOENCODING", "utf-8")
                .env("PYTHONUNBUFFERED", "1");
            process
        } else {
            // Installer: the frozen interpreter, dependencies, and GGUF are
            // installed beside the desktop app. Never fall back to system
            // Python or a remotely hosted model.
            let resources = bundle_resource_dir(app)?;
            let executable = resources.join("bridge").join(BRIDGE_FILE);
            let model = bundled_model_path(app)?;
            if !executable.is_file() {
                return Err(format!(
                    "Offline AI runtime is missing: {}. Reinstall Silabs Humanizer.",
                    executable.display()
                ));
            }
            if !model.is_file() {
                return Err(format!(
                    "Bundled Qwen model is missing: {}. Reinstall the complete offline edition.",
                    model.display()
                ));
            }
            let mut process = Command::new(executable);
            process.current_dir(&resources)
                .env("SILABS_HUMANIZER_MODEL_PATH", model)
                .env("PYTHONUTF8", "1")
                .env("PYTHONIOENCODING", "utf-8")
                .env("PYTHONUNBUFFERED", "1");
            process
        };

        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|err| format!("Cannot launch offline AI runtime: {err}"))?;
        let input = child.stdin.take().ok_or("Offline AI stdin unavailable")?;
        let output = child.stdout.take().ok_or("Offline AI stdout unavailable")?;
        Ok(Self { child, input, output: BufReader::new(output) })
    }

    fn send(&mut self, payload: Value) -> Result<Value, String> {
        let request = serde_json::to_string(&payload)
            .map_err(|err| format!("Cannot serialize request: {err}"))?;
        self.input
            .write_all(format!("{request}\n").as_bytes())
            .and_then(|_| self.input.flush())
            .map_err(|err| format!("Local Python bridge write failed: {err}"))?;

        let mut line = String::new();
        let count = self.output.read_line(&mut line)
            .map_err(|err| format!("Local Python bridge read failed: {err}"))?;
        if count == 0 {
            return Err("Local Python bridge stopped unexpectedly.".to_owned());
        }
        let reply: Value = serde_json::from_str(&line)
            .map_err(|err| format!("Invalid local Python bridge response: {err}"))?;
        if reply.get("ok").and_then(Value::as_bool) != Some(true) {
            return Err(reply.get("error").and_then(Value::as_str)
                .unwrap_or("Local operation failed").to_owned());
        }
        reply.get("data").cloned().ok_or("Missing response data".to_owned())
    }
}

impl Drop for BridgeProcess {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

#[derive(Default)]
struct BridgeState(Arc<Mutex<Option<BridgeProcess>>>);

#[tauri::command]
async fn bridge(
    payload: Value,
    app: AppHandle,
    state: State<'_, BridgeState>,
) -> Result<Value, String> {
    let shared = Arc::clone(&state.0);
    tauri::async_runtime::spawn_blocking(move || {
        let mut lock = shared.lock().map_err(|_| "Local bridge lock unavailable")?;
        if lock.is_none() {
            *lock = Some(BridgeProcess::start(&app)?);
        }
        let result = lock.as_mut().ok_or("Local bridge not started")?.send(payload);
        if let Err(ref message) = result {
            if message.contains("bridge read failed")
                || message.contains("bridge write failed")
                || message.contains("bridge stopped")
                || message.contains("Invalid local Python bridge response")
            {
                *lock = None;
            }
        }
        result
    })
    .await
    .map_err(|err| format!("Local bridge task failed: {err}"))?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(BridgeState::default())
        .invoke_handler(tauri::generate_handler![bridge, runtime_info])
        .run(tauri::generate_context!())
        .expect("failed to start Silabs Humanizer desktop");
}
