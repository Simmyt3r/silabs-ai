# Silabs Humanizer v0.2.0 - Desktop usability recovery

## Why this release exists

The first real Windows testing identified three severe blockers:

- The frozen Python bridge sometimes failed to return valid UTF-8, making the user refresh.
- Small-model output could include the instruction "Return only the rewritten text."
- DOCX body paragraphs were needlessly locked when they contained multiple Word formatting runs.

The initial side-by-side card workflow was also inconvenient for real document editing.

## Fixed in source code

- Force UTF-8 for frozen Windows Python and escape all non-ASCII values in JSON-lines IPC.
- Reject local model output that echoes prompt instructions.
- Move response formatting instructions before user text to reduce output contamination.
- Allow normal text-only multi-run Word paragraphs, text-only headings, and table cells to be revised.
- Preserve untouched formatting runs when exporting accepted DOCX edits.
- Keep hyperlinks, drawings, Word fields, and other complex structures read-only until full fidelity is tested.
- Allow numbered lists in AI output while blocking newly invented numerical claims.
- Switch to a continuous page-like editor with direct typing and selection-specific rewriting.
- Add a right-side offline writing assistant: correctness/clarity hints, one-click safe fixes,
  style/tone selection, reviewable AI suggestions and Accept/Reject/Restore.
- Keep the original file unmodified; only export approved working-copy changes into a new file.
- Add regression tests for Windows Unicode, prompt echo, run-preserving export, local hints,
  direct typing, selected-phrase rewriting and native Windows packaging.

## Boundaries

The on-device instant checker detects common repeated words, spacing,
punctuation and lengthy sentences. The native WebView enables spellcheck if an
OS dictionary is available. This is **not Grammarly itself** and does not yet
match its commercial grammar, style, tone or plagiarism coverage.

It remains a preview. Changing rich DOCX text can affect local formatting
in replaced regions; unchanged text retains its original runs. Always review
the exported document. Unsupported complex structures remain protected.

The local 1.7B model cannot guarantee grammatical correctness, meaning,
source fidelity or natural phrasing. A failing suggestion is blocked, not
silently accepted.

## Acceptance gates

- [x] Added backend and UI regressions for reported failures
- [ ] All v0.2.0 GitHub Actions checks green
- [ ] Full GGUF offline Windows v0.2.0 installer built
- [ ] Fresh installed-runtime Qwen smoke passes
- [ ] Test genuine 50-200 page Word documents on the user's computer
- [ ] Confirm UI without refresh, selection editing and normal workflow
- [ ] Review rendering at 100% and 125% Windows scaling
- [ ] Test full offline operation and CPU/memory usage

Do not use the v0.1.x installer for this release's improvements.
