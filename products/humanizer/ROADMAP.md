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
- [x] Selection-based rewriting and in-place editing of text-only paragraphs
- [ ] Full rich-text character-level editing of Word objects
- [x] Side-by-side comparison with basic change highlighting
- [ ] Full multi-change diff and rich-text editing
- [x] Accept/reject/restore whole-paragraph suggestions in desktop preview
- [x] DOCX export to a NEW file with run-aware changes for plain text-only multi-run paragraphs
- [x] Offline packaging script, bundled-runtime paths, model verification and NSIS configuration
- [x] v0.1.x model-bundled installer successfully built and tested on clean Windows runner
- [ ] v0.2.0 model-bundled installer successfully built and tested
- [x] Windows Tauri native CI compilation
- [x] Automated clean Windows installer validation for v0.1.x
- [ ] v0.2.0 real Windows GUI acceptance
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

## Screenshot-driven v0.2.0 recovery (2026-10-20)
- [x] Fix CP1252/UTF-8 JSON protocol errors on Windows.
- [x] Reject leaked LLM instructions such as "Return only the rewritten text."
- [x] Support normal multi-run DOCX paragraphs, headings, and table text safely.
- [x] Permit structural list numbering without allowing invented numeric facts.
- [x] Continuous editing workspace with selected-text rewrites.
- [x] Immediate local correctness/clarity hints and one-click corrections.
- [x] Automated tests for Unicode, draft selection, hints and run preservation.
- [ ] v0.2.0 full offline build and installed runtime check.
- [ ] Positive user evaluation and real-document UX sign-off.


## v0.3.0 offline writing intelligence
- [x] Explainable English grammar/usage checks and direct apply controls.
- [x] Ranked English spelling suggestions using an embedded frequency lexicon.
- [x] Optional Qwen-driven deeper grammar rewriting within existing review workflow.
- [x] Explicitly selected local document source comparison using 8-word sequences.
- [x] Match excerpts, per-source and aggregate match coverage, no plagiarism verdict.
- [x] No network connection, external index, document upload or background folder scan.
- [x] Python API, desktop integration and local-source validation tests.
- [x] Package wordfreq and RapidFuzz dependencies into offline builder.
- [ ] v0.3 full Windows offline installer and installed-runtime acceptance checks.
- [ ] Grammar precision/recall evaluation for British English and technical texts.
- [ ] Human user acceptance, installer signing and final redistribution licence review.

See [OFFLINE_LANGUAGE_AND_SIMILARITY.md](desktop/OFFLINE_LANGUAGE_AND_SIMILARITY.md).

## 2026-10-20: grammar QA and Windows remediation

- [x] Added academic subject-verb checks and quotation/URL/DOI protection.
- [x] Added protected Nigerian/British/academic vocabulary and explicit common typos.
- [x] Curated QA: 0/35 valid samples flagged, 6/6 typo and 7/7 grammar examples.
- [x] Discovered actual installed-v0.3.x missing-wordlist failure on Windows.
- [x] Explicitly bundle English wordfreq msgpack and fail release if frozen spelling fails.
- [x] Add real dictionary diagnostics in desktop Model settings.
- [x] Add local Windows private smoke script and test instructions.
- [ ] Verify patched v0.3.2 installer in **fresh installed** Windows runtime.
- [ ] Run full GUI usability and scaling evaluation on user's physical laptop.
