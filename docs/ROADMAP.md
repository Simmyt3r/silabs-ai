# Silabs AI Roadmap

## Phase 0 - Engine foundation

- [x] clean repository structure
- [x] configurable pretrained-model engine
- [x] lazy inference loading
- [x] versioned FastAPI interface
- [x] LoRA/full-SFT training entrypoint
- [x] dataset normalization and validation
- [x] behavioral regression harness
- [x] CI and unit tests
- [x] RAG extension interface
- [x] engineering documentation

## Phase 1 - Reconnect the finalized corpus

- [x] rebuild public source data in GitHub Actions
- [x] validate against the canonical schema
- [x] regenerate source/download manifest
- [x] rerun exact and same-input leakage checks
- [x] freeze a reproducible v1 research dataset artifact
- [x] generate deterministic 400/100 smoke subsets
- [x] validate a commercially screened corpus release

Research rebuild: 122,473 total records, 120,024 train, 2,449 dev,
zero same-input train/dev leakage.

Commercially screened rebuild: 105,842 total records, 103,725 train, 2,117 dev.
SciQ and OpenBookQA are excluded pending suitable commercial-use clearance.

Exit criterion: one reproducible, auditable corpus approved for research
training. **Complete.**

## Phase 2 - Baseline

- [x] download and full-load the untouched base model in a clean runner
- [x] expand deterministic behavioral evaluation
- [x] add academic/reasoning/coding cases
- [x] freeze the successful baseline report and score

Current engine baseline: 19/20 (95.0%) with the concise Silabs runtime
contract. Strict-format cases now pass; the remaining miss is one simple
transitive comparison case.

Exit criterion: measurable baseline before Silabs fine-tuning. **Complete.**

## Phase 3 - Training

- [x] add deterministic smoke-subset generation
- [x] add 100/25 and 400/100 LoRA smoke recipes
- [x] add base-versus-candidate report comparison
- [x] run smoke experiments on finalized research corpora
- [x] evaluate smoke checkpoints
- [x] preserve long-example assistant tokens during SFT truncation
- [x] inspect train/eval loss and checkpoint behavior
- [x] retain experiment metadata and rejected-candidate records
- [ ] validate the conservative commercial-profile smoke recipe
- [ ] select the first no-regression candidate recipe
- [ ] run LoRA SFT on the full commercially screened corpus

Fast 100/25 experiment: 90% -> 95%, zero regressions.
Extended 400/100 research experiment: 90% -> 85%, rejected for two regressions.

Exit criterion: candidate Silabs AI v1 adapter that passes the expanded
promotion gate.

## Phase 4 - Evaluation and promotion

- [x] base-versus-candidate comparison tooling
- [x] 50-case conversation/math/science/reasoning/coding/instruction suite
- [x] repetition/degeneration checks
- [x] reusable zero-regression promotion gate
- [x] combined capability + safety release gate
- [x] reject one regressing 400-example candidate
- [x] add 12-case safety/uncertainty suite
- [x] add deterministic pre-inference runtime guardrails
- [x] reach 12/12 on the engine-level guardrail regression suite
- [ ] validate conservative commercial candidate on the 50-case suite
- [ ] evaluate raw model safety with runtime guardrails disabled
- [ ] conduct manual response-quality and safety review
- [ ] approve or reject the first release candidate

Exit criterion: named and versioned release candidate.

## Phase 5 - RAG

- [ ] select retrieval backend
- [ ] build ingestion pipeline
- [ ] source-aware retrieval
- [ ] citation-capable generation
- [ ] retrieval-quality evaluation

## Phase 6 - Product integration

- [ ] authentication and API keys
- [ ] streaming
- [ ] rate limiting
- [ ] observability
- [ ] UniXpress integration
- [ ] reusable client/SDK
- [ ] deployment benchmark and quantization

## Later

Larger models, multilingual expansion, tool use, vision and domain adapters should be added because evaluations and product requirements justify them, not because architecture diagrams look more impressive with extra boxes.
