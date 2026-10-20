# Silabs Humanizer: Offline language QA and Windows acceptance

Date: 2026-10-20

## What changed

The grammar checker now includes targeted academic singular/plural subject–verb
agreement patterns, plus existing article, auxiliary, modal, tense, comparison,
demonstrative and uncountable-noun corrections.

The spelling checker protects a curated set of legitimate Nigerian terms,
British spellings and academic/technical vocabulary. It also explicitly
handles common misspellings that are too frequent in ordinary word corpora
to trigger a simple "unknown word" detector.

Quotation, backtick-code, email, URL and DOI spans are skipped by automated
grammar/spelling replacements. All corrections remain opt-in.

## Reproducible language QA

Command:

~~~shell
python -m products.humanizer.tests.language_benchmark
~~~

Evidence from passing GitHub Actions foundation run:
https://github.com/Simmyt3r/silabs-ai/actions/runs/39386489903

| Curated sample | Result |
|---|---:|
| Valid English sentences assessed | 35 |
| Sentences falsely flagged by spelling engine | 0 / 35 (0%) |
| Deliberately misspelled words correctly suggested | 6 / 6 (100%) |
| Deliberately incorrect grammar forms recognized | 7 / 7 (100%) |

The initial smoke run incorrectly flagged **standardise** and missed
**goverment** and **recieve**; these were corrected before the passing run.

These measurements are **not** population-level precision, recall or accuracy.
They are a small, hand-constructed regression suite. They cannot establish
performance on all Nigerian languages, large academic manuscripts or genuine
student prose. More blind reviewer-labeled testing is required.

## Automated Windows acceptance

GitHub Actions:
- Frozen Windows executable: imports a DOCX file.
- Frozen Windows executable: confirms offline grammar and spelling.
- Frozen Windows executable: checks only explicitly selected local sources.
- Native Tauri Windows build: compiles.
- Complete offline installer: packages Qwen GGUF, WebView2 and local runtime.
- Separate clean-install run: installs actual NSIS executable, checks model hash,
  runs local Qwen rewrite, exports DOCX and TXT without damaging originals.

This tests Windows runners, **not the user's own PC**. The app's visual
workflows, screen scaling, interactive file dialogs and perceived speed
remain user acceptance steps.

### Safely test on a physical Windows 10/11 PC

Download [TEST_ON_YOUR_WINDOWS_PC.ps1](TEST_ON_YOUR_WINDOWS_PC.ps1).
Locate the installed app folder (right-click its Windows shortcut and
choose **Open file location**). The folder should contain the app executable,
the `bridge` and `model` subfolders.

With Wi-Fi disconnected, open PowerShell, change to the folder holding the
downloaded script, and run:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\TEST_ON_YOUR_WINDOWS_PC.ps1" -InstallDir "C:\FULL\PATH\TO\Silabs Humanizer" -RunInference
~~~

The script uses synthetic TXT data in a temporary folder. It never opens
your real documents, uploads data, modifies the installed application,
or requires a system Python installation. It verifies installed checks,
source similarity, export integrity, and optionally real Qwen CPU inference.
The benchmark above is a separate test run by GitHub CI.

Do not share full machine paths, account information, or sensitive document
content when reporting results. A screenshot of PASS/FAIL lines is sufficient.

## Further quality gates

- Curate a separate blind set of genuine Nigerian university writing,
  with permission and sensitive details removed.
- Evaluate false positives per 1,000 words and by subdomain, not just
  per canned sentence.
- Test with user dictionary controls for genuine technical terms.
- Measure correction quality with independent human reviewers, not just
  a rule-trigger benchmark.
- Observe CPU and memory impact on an 8GB Windows laptop and review
  output in actual Microsoft Word.

Neither the rule-based grammar checker nor Qwen3-1.7B guarantees
Grammarly-equivalent grammar accuracy.
