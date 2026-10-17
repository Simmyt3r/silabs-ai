# Offline Windows installer: Release candidate process

This project supports a self-contained **Windows NSIS installer** containing:
the Tauri desktop application, a frozen Python/llama.cpp bridge, a verified
Qwen3-1.7B GGUF model file and the WebView2 offline installer.

**Status:** Installer construction is implemented but not yet verified on
a clean disconnected Windows machine. It is not an approved public release.

## Build environment (internet allowed)

Use Windows x64 with Node.js 20+, npm, Rust/MSVC, Python 3.11, the standard
Tauri Windows build prerequisites, PyInstaller, python-docx and a compatible
`llama-cpp-python` installation.

Build-only dependencies may be fetched online while assembling the installer.
**The installed app performs no runtime downloads or remote inference.**

From repository root, in PowerShell:

~~~powershell
python -m pip install -r products/humanizer/requirements.txt
python -m pip install pyinstaller llama-cpp-python
~~~

Place an authorised, locally stored Qwen3-1.7B GGUF file on the build machine.
Review the model licence, GGUF converter licence, native dependency
redistribution terms and source provenance before distributing binaries.

**Use a checksum from the trusted source of the weights.** Hashing an
unverified local file and trusting that same value is not an integrity check.

~~~powershell
cd products/humanizer/desktop
.\build-offline-windows.ps1 -ModelPath "D:\Models\qwen3-1.7b-q4.gguf" -ModelSha256 "TRUSTED_64_CHAR_SHA256" -LicenseReviewed
~~~

The script stops if:
- the model is missing, too small, not GGUF, or has the wrong SHA-256
- the developer has not explicitly confirmed the redistribution review
- Python, PyInstaller, npm or Rust prerequisites are missing
- the frozen bridge process does not answer the JSON-lines smoke test
- the model copy differs from the original file
- the Vite or Tauri/NSIS build fails or installer is not produced

Build output:

~~~text
products/humanizer/desktop/src-tauri/target/release/bundle/nsis/
~~~

The installer uses `webviewInstallMode: offlineInstaller`, which embeds an
offline WebView2 installer for machines that do not already have it.
The compiler/build process may download the installer while packaging, but
**installation of the resulting setup executable can be offline**.

## Release packaging structure

~~~text
Silabs Humanizer (NSIS)
  |- Tauri desktop executable
  |- resources/bridge/silabs-humanizer-bridge.exe
  |- resources/model/qwen3-1.7b.gguf
  |- resources/model/manifest.json
  |- embedded WebView2 offline runtime installer
~~~

At runtime Tauri loads the bundled executable and model from its installed
resources directory. There is no fallback to a system Python interpreter or
remote service in release mode. The GUI automatically selects the local
bundled GGUF resource.

## Release acceptance tests

1. Install on a freshly provisioned Windows 10/11 x64 PC, with **no network**.
2. Confirm installer does not request model or WebView2 downloads.
3. Open DOCX, TXT and Markdown documents.
4. Run a true Qwen rewrite with the bundled GGUF while offline.
5. Verify citations, numbers, names, qualifications and meaning.
6. Accept/reject a revision and export a NEW document.
7. Confirm the original file remains byte-for-byte unchanged.
8. Reopen exported file with Microsoft Word and compare structure.
9. Check cold start, warm rewrite, CPU/RAM/disk load on an 8GB laptop.
10. Inspect bundled DLLs, antivirus flags, code signing and dependency licences.

A PyInstaller smoke test alone does **not** validate real local inference.
Complex DOCX content is intentionally read-only until rich-format preservation
has been implemented and regression-tested.

## Security and distribution

- No remote AI endpoint, telemetry or document uploading.
- Model and runtime are local installer resources.
- Source documents are never overwritten.
- Existing user documents are protected by source fingerprints and review.
- No raw model file is committed to GitHub.
- A signed installer and a clean offline VM acceptance test remain mandatory
  before calling this production-ready.
