# Silabs Humanizer Roadmap

## v0.1 Foundation
- [x] Product structure
- [x] Preservation engine skeleton
- [x] Rewrite pipeline skeleton
- [x] Critic skeleton
- [x] Style profile skeleton
- [x] Implement local model adapters (GGUF + existing Transformers engine; device smoke test pending)
- [x] Conservative DOCX/TXT/MD import (complex DOCX formatting read-only)
- [ ] Rich-text desktop editor
- [ ] Selection-based rewrite actions
- [ ] Side-by-side diff
- [ ] Accept/reject changes
- [x] Conservative DOCX export to a NEW file (simple single-run paragraphs only)
- [ ] Offline installer
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
