# Install Silabs Humanizer on Windows: offline release candidate

**Release candidate build: PASS. Automated clean Windows installation: PASS.**
Graphical desktop usage on a physically disconnected Windows PC is not yet
validated. The installer remains an engineering release candidate.

Built artifact and checksums:
https://github.com/Simmyt3r/silabs-ai/actions/runs/39261178457

Fresh Windows installer acceptance evidence:
https://github.com/Simmyt3r/silabs-ai/actions/runs/39268760789

The acceptance workflow downloaded this exact installer, verified its SHA-256,
installed it into a new folder, confirmed the local model and Tauri executable
were installed, generated a real CPU-only Qwen rewrite, and verified DOCX and
TXT exports without changing original files.

Build status and downloadable artifact:
https://github.com/Simmyt3r/silabs-ai/actions/workflows/humanizer-offline-installer.yml

## Before installing

- Windows 10 or 11, x64.
- Recommended: at least 8 GB RAM; 16 GB preferred.
- Allow several GB of free disk space for installer and extracted model.
- Expect CPU-only rewriting to take time on older laptops.
- This is an unsigned engineering release candidate, not a signed production release.

## Download the installer

1. Open a successful GitHub Actions run titled Humanizer full offline Windows installer.
2. Scroll to Artifacts.
3. Download Silabs-Humanizer-Windows-Offline-Installer-RC.
4. Extract the downloaded ZIP.
5. Verify the setup executable checksum against SHA256SUMS.txt:

~~~powershell
Get-FileHash .\*setup.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
~~~

Compare the digest to the checksum line. Only run the installer when they
match. Do not install binaries from unknown third-party mirrors.

## Install and test offline

1. Disconnect from Wi-Fi or Ethernet before running the installer.
2. Run the setup.exe executable from the extracted folder.
3. Follow the installer instructions. The setup includes the local model
   and the offline WebView2 installer; it should not need a network connection.
4. Launch Silabs Humanizer.
5. Open a sample DOCX, TXT or Markdown file.
6. Select an editable paragraph, choose a rewriting mode, and click Generate.
7. Check the suggested rewrite for altered meaning, facts, or references.
8. Accept the suggestion and choose Export revised file.
9. Open the exported document and confirm content and formatting.
10. Verify the original source file remains unchanged.

Stop testing and report the exact error if setup needs internet access,
the model is missing, the app crashes, or export damages formatting.

## Known constraints

- The first model load can be slower than later rewrites.
- Richly formatted Word paragraphs may be read-only in this preview.
- This is not yet a complete Word-compatible editor.
- Inference runs locally, not over the internet.
- Clean-machine acceptance testing is still needed for production approval.

## Third-party provenance

Qwen model weights: ggml-org/Qwen3-1.7B-GGUF, Q4_K_M.
Apache-2.0 on model card:
https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF

Pinned model SHA-256:
d2387ca2dbfee2ffabce7120d3770dadca0b293052bc2f0e138fdc940d9bc7b5

Local inference runs with llama-cpp-python / llama.cpp.
Review other dependency licensing and notices before distributing.

## Confirmed automated clean-install checks (2026-10-19)

- [x] Installer SHA-256 verified against included SHA256SUMS.txt.
- [x] NSIS silent installation succeeded on a fresh Windows GitHub runner.
- [x] The Tauri executable, frozen bridge, local GGUF and manifest were installed.
- [x] Installed model SHA-256 matches the trusted published digest.
- [x] Installed GGUF actually produced an offline CPU rewrite.
- [x] DOCX export opened successfully and preserved a heading and unchanged citation paragraph.
- [x] TXT export succeeded without overwriting its original file.
- [ ] Interactive desktop UI acceptance on a user's PC.
- [ ] Disconnect Wi-Fi and verify installation and desktop inference manually.
- [ ] Low-memory / slow-CPU performance and Windows Defender review.

This CI runner did not simulate a disconnected network interface.
Use the checklist above to complete the real offline acceptance gate.
