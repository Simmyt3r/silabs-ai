# Silabs Humanizer v0.1.1 - Windows offline release candidate

## Changes since v0.1.0

This release candidate improves the **existing** desktop editing workflow
without adding unrelated product features.

- Integrated UI regression tests now cover opening files, generating suggestions,
  accepting/rejecting edits, exporting, and cancelling an unsaved document switch.
- Added a **Model settings > Check local setup** action to verify that the GGUF
  weights, local inference library, and Word document support exist.
- Setup diagnostics never load a document, transmit data, download dependencies,
  or generate text. They do not claim to validate model quality.
- Clearer explanations when local weights or libraries are missing.
- Visible CPU processing guidance for first-run local Qwen inference.
- Added deterministic backend tests for missing/invalid local weights and
  no-inference diagnostic behavior.

## Included offline runtime

Windows x64 Tauri shell, bundled PyInstaller Python runtime, llama.cpp
inference, GGUF Qwen3-1.7B Q4_K_M model, and WebView2 offline installer.

The original document remains unchanged. Revisions require explicit approval
before they can be exported into a separately named file.

## Release gates

- [x] Unit tests for preservation, document parsing and exporting
- [x] Desktop UI component tests and editing lifecycle tests
- [ ] v0.1.1 native build and complete installer packaging
- [ ] v0.1.1 installed-runtime smoke with real Qwen model
- [ ] Human keyboard, scaling, first-run and file-dialog testing on Windows
- [ ] Physically disconnected Windows installation and measured CPU/RAM usage
- [ ] Authenticode signing and final distribution approval

## Notes

v0.1.0 was built and validated on a fresh Windows GitHub runner:
https://github.com/Simmyt3r/silabs-ai/actions/runs/39268760789

**That prior installer does not contain v0.1.1 changes.** Download the v0.1.1
artifact only from a successful v0.1.1 installer workflow run.
