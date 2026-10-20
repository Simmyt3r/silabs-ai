# Silabs Humanizer v0.3.2: Windows test checklist

This candidate replaces v0.3.0/v0.3.1 packaging. It includes academic
grammar patterns and corrections for an incomplete Windows spelling lexicon.
The older v0.3.1 build was observed to fail after installation with:
"No wordlist 'best' available for language 'en'".

The updated installer MUST pass these release gates before user distribution:

1. Build-time inspect installed wordfreq/data for English msgpack gzip files.
2. Explicitly package English files under wordfreq/data in the frozen runtime.
3. Run analyse_writing on the actual frozen bridge, and stop packaging
   if both grammar and spelling results are not returned.
4. Download installer, verify SHA-256, then install on a fresh Windows runner.
5. Run installed grammar/spelling, local reference similarity,
   real Qwen inference, DOCX import/export and TXT import/export tests.
6. Confirm the source file is unchanged.

## Private PC smoke test without Python

1. After installation, locate the app folder through the Windows shortcut.
2. Disconnect Wi-Fi.
3. Download TEST_ON_YOUR_WINDOWS_PC.ps1 from the repository (a plain-text
   PowerShell script; review it before running).
4. In PowerShell run:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\TEST_ON_YOUR_WINDOWS_PC.ps1" -InstallDir "C:\path\to\Silabs Humanizer" -RunInference
~~~

The script verifies the bundled GGUF model's checksum, spelling,
grammar, selected-file source matching, non-destructive export and
optional offline local model rewrite. It uses synthetic data and
cleans up its temporary files.

## Manual GUI and document acceptance (must be done on the actual laptop)

- [ ] Launch offline without a Python or network prompt.
- [ ] Open a substantial DOCX file and confirm headings and paragraphs scroll.
- [ ] Select a previously blocked but text-only mixed-format paragraph and edit.
- [ ] Use the Grammar tab to approve a suggested correction.
- [ ] Check ordinary technical/Nigerian words are not inappropriately corrected.
- [ ] Use the Sources tab to select a synthetic reference file and see matched text.
- [ ] Use Rewrite on a highlighted phrase and Accept/Reject proposals.
- [ ] Export a separately named DOCX, reopen in Word, inspect tables and headings.
- [ ] Confirm original source untouched and no compulsory refresh.
- [ ] Run at normal and 125% Windows display scaling and note sluggish controls.
- [ ] If the model is too slow on CPU, record cold and warm generation seconds.

The Windows runner cannot certify interactive UX on this particular laptop.
Until the user's checks pass, this remains an engineering release candidate.

## Measured small lexical regression

CI result: https://github.com/Simmyt3r/silabs-ai/actions/runs/39386489903

- Curated valid academic/Nigerian/British samples: 35.
- Samples incorrectly flagged by spelling: 0 / 35.
- Deliberate typo examples identified: 6 / 6.
- Deliberate grammar examples identified: 7 / 7.

These deliberately curated tests are not statistically representative.
See LANGUAGE_QA_AND_WINDOWS_TEST.md.
