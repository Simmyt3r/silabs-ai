# Silabs Humanizer Roadmap

## v0.1 Foundation
- [x] Product structure
- [x] Preservation engine skeleton
- [x] Rewrite pipeline skeleton
- [x] Critic skeleton
- [x] Style profile skeleton
- [ ] Connect local model runtime
- [ ] DOCX/TXT/MD parser
- [ ] Rich-text desktop editor
- [ ] Selection-based rewrite actions
- [ ] Side-by-side diff
- [ ] Accept/reject changes
- [ ] DOCX export
- [ ] Offline installer

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
