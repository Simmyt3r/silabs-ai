use serde_json::Value;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::State;

struct BridgeProcess {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
}

impl BridgeProcess {
    fn start() -> Result<Self, String> {
        // Development preview: use the repository Python environment.
        // The release installer will bundle an offline sidecar instead.
        let python = std::env::var("SILABS_HUMANIZER_PYTHON")
            .unwrap_or_else(|_| "python".to_owned());
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../../..")
            .canonicalize()
            .map_err(|err| format!("Cannot locate Silabs AI repository: {err}"))?;

        let mut process = Command::new(python)
            .arg("-u")
            .arg("-m")
            .arg("products.humanizer.service.desktop_bridge")
            .current_dir(&root)
            .env("PYTHONPATH", &root)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|err| format!("Cannot start local Python service: {err}"))?;
        let input = process.stdin.take().ok_or("Python stdin unavailable")?;
        let output = process.stdout.take().ok_or("Python stdout unavailable")?;
        Ok(Self {
            child: process,
            input,
            output: BufReader::new(output),
        })
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
async fn bridge(payload: Value, state: State<'_, BridgeState>) -> Result<Value, String> {
    let shared = Arc::clone(&state.0);
    tauri::async_runtime::spawn_blocking(move || {
        let mut lock = shared.lock().map_err(|_| "Local bridge lock unavailable")?;
        if lock.is_none() {
            *lock = Some(BridgeProcess::start()?);
        }
        let result = lock.as_mut().ok_or("Local bridge not started")?.send(payload);
        // Restart after pipe/protocol failure, not after ordinary validation
        // failures: those do not terminate the Python model process.
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
        .invoke_handler(tauri::generate_handler![bridge])
        .run(tauri::generate_context!())
        .expect("failed to start Silabs Humanizer desktop");
}
