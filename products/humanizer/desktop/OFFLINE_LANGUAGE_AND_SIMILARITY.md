# Silabs Humanizer: Offline language and source review (v0.3.0 candidate)

## Three separate functions

### 1. English grammar review

The **Grammar** tab checks a passage with high-confidence local rules,
including:
- singular/plural demonstratives (This sentences -> These sentences)
- incorrect auxiliary forms (doesn't has -> doesn't have)
- some common past-tense/past-participle errors
- some singular/plural existential constructions
- selected irregular uncountable nouns
- limited a/an usage with sound-based exceptions

A dedicated option opens **Qwen Grammar** mode for a slower, more contextual
sentence-level revision. The model can make mistakes; its proposal must pass
protection checks and be explicitly accepted.

The local rules are helpful but **not a comprehensive grammatical parser**.
The current small offline model is not equivalent to Grammarly's large
commercial grammar service.

### 2. Offline English spelling suggestions

Uses **wordfreq**'s embedded English frequency data and **RapidFuzz** to
rank up to four possible alternatives per unfamiliar word. Unknown names,
regional words and technical terms may be valid. It excludes title-cased
names by default to limit false positives. It never silently autocorrects.

The bundled lexicon is included at **installer build time**.
The installed application does not download word lists.

Third-party attribution:
- wordfreq (Apache-2.0 for software; CC BY-SA 4.0 and other documented
  attribution requirements for embedded data)
  https://github.com/rspeer/wordfreq
- RapidFuzz (MIT)
  https://github.com/rapidfuzz/RapidFuzz

Keep original third-party licence and attribution files in distribution.

### 3. Local reference similarity (not universal plagiarism detection)

The **Sources** tab opens a Windows picker. The user explicitly selects
one or more local DOCX, TXT, or Markdown reference documents.

The checker normalises words and detects overlapping exact **8-word
sequences**. It reports total matched word coverage, individual source
filenames, percentages within the draft and example matching passages.

**This cannot assert plagiarism or prove originality.** It does not search
websites, journal databases, academic repositories, commercial plagiarism
indexes or documents not explicitly selected. Properly cited quotes and
common phrases can legitimately overlap. It cannot reliably identify
paraphrased passages or semantic copying.

An offline universal plagiarism detector is not technically possible without
a prebuilt or user-supplied reference corpus.

## Security and privacy

- No document upload, telemetry, accounts or network requests.
- Source matching uses only selected local paths; no automatic folder scans.
- It prevents self-comparison and checks source fingerprints.
- The report does not change the document.
- Grammar and spelling revisions are offered, never auto-applied.

## Acceptance tests

- [x] Grammar and spelling API and UI integration
- [x] Source similarity API and UI integration
- [x] Test high-confidence rules and spell suggestions
- [x] Test explicit source comparison and self-match rejection
- [x] Include embedded dictionary in offline installer build instructions
- [ ] Full model-bundled Windows installer compiled with language dictionaries
- [ ] Fresh-Windows installed-runtime language/source tests
- [ ] Human editing experience with multiple real DOCX files
- [ ] Independent language accuracy and false-positive evaluation
- [ ] Installer redistribution notices and signing review

The source code is a v0.3.0 **engineering candidate** until those
installation and quality gates pass.
