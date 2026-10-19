# Silabs Humanizer Roadmap

## v0.1 Foundation
- [x] Product structure
- [x] Preservation engine skeleton
- [x] Rewrite pipeline skeleton
- [x] Critic skeleton
- [x] Style profile skeleton
- [x] Implement local model adapters (GGUF + existing Transformers engine; device smoke test pending)
- [x] Conservative DOCX/TXT/MD import (complex DOCX formatting read-only)
- [x] Tauri + React desktop workspace shell (engineering preview)
- [ ] Full rich-text desktop editor
- [x] Selected-paragraph rewrite actions in desktop preview
- [ ] Selection within paragraphs and rich-text editing
- [x] Side-by-side comparison with basic change highlighting
- [ ] Full multi-change diff and rich-text editing
- [x] Accept/reject/restore whole-paragraph suggestions in desktop preview
- [x] Conservative DOCX export to a NEW file (simple single-run paragraphs only)
- [x] Offline packaging script, bundled-runtime paths, model verification and NSIS configuration
- [ ] Build and verify a complete offline installer with real model weights
- [x] Windows Tauri native CI compilation
- [ ] Standalone Windows app testing on a clean offline machine
- [x] Real Qwen3 local smoke-test runner implemented
- [ ] Execute real Qwen3 benchmark and manually review rewrite quality
- [ ] Rich DOCX run/hyperlink preservation
- [ ] Header/footer, footnote, track-changes and textbox handling

## v0.2 Quality
- [ ] Naturalness scoring
- [ ] Repetition scoring
- [ ] Readability scoring
- [ ] Citation/fact preservation tests
- [ ] Full-document chunking
- [ ] Consistency pass
- [ ] Batch rewrite

## v0.3 Model optimization
- [ ] Curate humanization training pairs
- [ ] Add negative preservation examples
- [ ] Train Humanizer LoRA
- [ ] Evaluate meaning preservation
- [ ] Convert validated model to GGUF
- [ ] Package llama.cpp runtime

## Non-negotiable release gates
- No silent citation changes
- No silent number changes
- No fabricated facts
- Offline operation must not require account or network access
- User can always review and reject model edits

## Current priority: UI/UX and structure freeze
- [x] Consolidate desktop workflow into one editing/review path
- [x] Centralize shared document and proposal state
- [x] Searchable document outline and clear read-only status
- [x] Consistent writing-focused styles and word-level comparison
- [x] Distinguish accepted versus exported revisions
- [x] Prevent silent loss of accepted edits on opening/closing
- [x] Add automated review/diff tests and UI audit checklist
- [ ] Hands-on Windows keyboard, zoom, performance and accessibility QA
- [ ] Review real GGUF output and document layout on a Windows laptop
- [ ] Resolve all issues from [UI_UX_AUDIT.md](desktop/UI_UX_AUDIT.md) before feature additions

## Installer acceptance (2026-10-19)
- [x] Complete NSIS release-candidate installer built and uploaded to GitHub Actions
- [x] Frozen CPU Qwen inference passed in packaged runtime
- [x] Fresh Windows runner installed the actual NSIS installer successfully
- [x] Installed GGUF checksum, DOCX/TXT export and untouched original files verified
- [ ] User's offline Windows desktop GUI acceptance and performance measurement
- [ ] Installer signing and wider distribution clearance

Evidence: https://github.com/Simmyt3r/silabs-ai/actions/runs/39268760789

## v0.1.1 UX validation

- [x] Realistic full desktop UI workflow tests with mocked Tauri file dialogs
  and local IPC, including blocked rewrites and unsaved-change cancellation.
- [x] On-device GGUF/header and inference/document-library diagnostic path.
- [x] CPU warm-up/first generation explanation in the editing interface.
- [ ] v0.1.1 full offline installer build and fresh Windows install acceptance.
- [ ] Manual interactive GUI testing, resource usage, and disconnected-PC
  acceptance before production sign-off.
