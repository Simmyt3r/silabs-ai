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

- [ ] place finalized train/dev data under ignored local storage
- [ ] validate against the canonical schema
- [ ] regenerate source manifest
- [ ] rerun leakage and quality checks
- [ ] freeze an exact v1 dataset release

Exit criterion: one reproducible, auditable corpus approved for training.

## Phase 2 - Baseline

- [x] download and full-load the untouched base model in a clean runner
- [x] expand deterministic behavioral evaluation
- [x] add academic/reasoning/coding cases
- [ ] freeze the successful baseline report and score

Exit criterion: measurable baseline before Silabs fine-tuning.

## Phase 3 - Training

- [ ] run a 100-500 record smoke experiment
- [ ] evaluate the smoke checkpoint
- [ ] run LoRA SFT on the finalized corpus
- [ ] inspect train/eval loss and checkpoints
- [ ] retain candidate metadata

Exit criterion: candidate Silabs AI v1 adapter.

## Phase 4 - Evaluation and promotion

- [ ] base-versus-candidate comparison
- [ ] conversation quality review
- [ ] math/science/reasoning evaluation
- [ ] instruction-following evaluation
- [ ] repetition/degeneration checks
- [ ] safety review
- [ ] approve or reject candidate

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
