# Humanizer desktop acceptance: reported issues from 2026-10-20

The attached real Windows screenshots reported a 3/10 experience. This is
a **release blocker**, not cosmetic feedback.

## Reproduced issues and source-code fixes

| Report | Root cause | Change |
|---|---|---|
| "Local Python bridge read failed: stream did not contain valid UTF-8" | frozen Python stdout and Windows locale disagreeing | force UTF-8 in Rust subprocess + bridge input/output and ASCII-safe JSON-lines protocol |
| README rewrite displayed "Return only the rewritten text." | small local LLM echoing a prompt tail | move instruction ahead of input; reject instruction echoes before presenting suggestions |
| Too many paragraphs locked | DOCX gate required exactly one `w:r` run | allow multiple plain text runs, editable headings and table cells; preserve untouched formatting |
| Five numbered security points blocked | every new digit considered a fabricated fact | allow structural numbered list prefixes while continuing to reject unverified quantitative claims |
| Had to refresh | error recovery was unclear and IPC could fail to decode Windows bytes | stabilize protocol, expose visible recoverable errors, keep the app's open-file workflow available |
| Document editing felt like a demo | navigation + original/proposal cards, no actual writing page | continuous document canvas, text editing, selection rewrite, assistant panel |
| Missing immediate grammar hints | model request required before every correction | local lightweight repeated-word, spacing, punctuation and long-sentence hints with one-click corrections |

## v0.2 workflow

1. Open a DOCX/TXT/Markdown document.
2. Scroll and click a paragraph or heading in the continuous reading canvas.
3. Edit the paragraph directly. Changes remain in memory until export.
4. Use Suggestions to apply clear, safe mechanical corrections instantly.
5. Optionally select a phrase, choose Rewrite and a style goal, then Generate.
6. Review before accepting; rejected suggestions do not touch your document.
7. Export a NEW document after reviewing accepted edits.

## Remaining limits

- Complex Word structures with hyperlink XML, drawing elements, fields, etc.,
  remain protected until preserving those exact structures is tested.
- The instant hint engine is **not** a full language parser or Grammarly's
  proprietary engine; spellcheck availability depends on Windows/WebView2.
- AI output quality still depends on a local 1.7B model. There is no guarantee
  a humanization pass is natural, factual or appropriate.
- Document-wide editing is a structured working-copy representation, not
  pixel-perfect live MS Word editing.
- Source code fixes do not repair the already-installed v0.1.1 binary.
  A new **v0.2.0** installer and fresh acceptance are required.

## Manual acceptance for the user's Windows PC

- [ ] Install v0.2.0 without Python and load a 150+ paragraph DOCX.
- [ ] Open/click/edit multi-run body paragraphs and headings.
- [ ] Ensure hyperlink/complex paragraphs explain why export is protected.
- [ ] Verify "Repeat repeat" one-click correction and spelling support.
- [ ] Select words in a paragraph and generate only a targeted rewrite.
- [ ] Verify no model instructions appear in the approved text.
- [ ] Verify numeric list items are not incorrectly rejected.
- [ ] Test original DOCX unchanged and Word opens the exported revision.
- [ ] Test a document containing accented letters, emojis and non-Latin scripts.
- [ ] Test app startup without any refresh, with network disconnected.
- [ ] Check screen layout on an 8GB RAM Windows 10 laptop.

Release remains a candidate until the user's actual desktop experience improves,
not simply until the CI checks are green.
