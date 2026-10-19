# Silabs Humanizer Desktop (Engineering Preview)

Tauri 2 + React + TypeScript workspace for the fully offline Humanizer product.

## Current capabilities

- Native picker for local DOCX, TXT and Markdown files
- Paragraph outline including headings and table cells
- Seven rewrite actions: Humanize, Academic, Grammar, Professional, Simplify, Shorten, Expand
- Choose an existing local Qwen3 GGUF model
- Side-by-side original/revision review
- Accept, reject and restore whole-paragraph changes
- Export accepted changes to a NEW file, never overwrite source
- Reject edits if the source file changes outside the editor (SHA-256 fingerprint)
- Persistent local model process across editing requests

**Limits:** This preview edits one whole simple paragraph at a time. Complex
Word formatting stays read-only. Real-model style and meaning validation
are not complete.

## Architecture

~~~text
React/TypeScript (local WebView)
  -> Tauri IPC
  -> Rust-managed persistent Python subprocess (JSON lines)
  -> offline parser / preservation / GGUF model
  -> proposed revision -> manual Accept/Reject -> export
~~~

No HTTP server, account, remote AI API, telemetry or cloud storage is required.

## Development setup

Prerequisites: Windows 10/11 with WebView2; Node.js 20+ and npm; Rust/MSVC
and Tauri Windows development prerequisites; Python 3.11 recommended;
an existing Qwen3-1.7B GGUF file and a compatible llama-cpp-python build.

From the repository root:

~~~powershell
python -m pip install -r products/humanizer/requirements.txt
python -m pip install llama-cpp-python
cd products/humanizer/desktop
npm install
npm run tauri dev
~~~

If the correct Python executable has a different path:

~~~powershell
$env:SILABS_HUMANIZER_PYTHON="C:\path\to\python.exe"
npm run tauri dev
~~~

Open the app, click Open document, choose a file, then Model settings >
Choose GGUF. Select a paragraph and rewrite mode. First inference may be
slow; subsequent edits reuse the same loaded process. Review proposals
before accepting. Export only writes a separate output file.

## Tests

~~~powershell
python -m pytest products/humanizer/tests -q
cd products/humanizer/desktop
npm run build
~~~

GitHub Actions checks Python regressions and React TypeScript builds.

## Release blockers

A standalone installer is not complete. The engineering preview requires
Python, dependencies and the GGUF model installed or stored on the developer
PC. Windows native compilation, Python/llama.cpp/model bundling, model
licence review, installer signing, resource benchmarks and real-document
quality testing remain outstanding.


## Standalone Windows installer preparation

See [OFFLINE_RELEASE.md](OFFLINE_RELEASE.md). A Windows packaging script
freezes the Python inference runtime, verifies the provided GGUF model by
SHA-256, and configures an NSIS installer with offline WebView2 dependencies.
The release app automatically discovers its bundled model and runtime.

The code for producing a full offline installer is implemented. **No installer
has been released yet.** The packaging step still needs a real authorised
GGUF model, execution of the Windows script, and clean disconnected-PC
acceptance testing.

## UI/UX architecture and acceptance

The desktop workspace has been reorganized into a single app shell, searchable document outline,
review component, dedicated state controller, and reusable review/diff helpers.
See [UI_UX_AUDIT.md](UI_UX_AUDIT.md) for the workflow and manual acceptance checklist.
Automated checks verify TypeScript compilation, review-state utilities and Windows build,
but do not replace actual hands-on usability testing.

## Long-document navigation and shortcuts

The outline displays an initial page of 80 paragraphs, with Show more for the next group. Search covers the full loaded document, not only visible entries.

Windows editing shortcuts: Ctrl+O opens a document, Ctrl+Enter generates a suggestion for the selected paragraph, Ctrl+Shift+S exports reviewed revisions, and Escape rejects the current suggestion. Keyboard shortcuts are ignored while typing in a text field.

Automated UI interaction tests exercise paging and search. Actual Windows usability, zoom, screen reader compatibility and performance checks remain open in [UI_UX_AUDIT.md](UI_UX_AUDIT.md).
