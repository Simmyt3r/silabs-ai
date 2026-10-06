# Silabs AI

Silabs AI is the shared AI engine for Silabs products. Version 1 moves the project from tiny from-scratch experiments to a reproducible pretrained-model fine-tuning architecture with inference, training, evaluation and future RAG behind one stable interface.

The first supported base model is `HuggingFaceTB/SmolLM2-360M-Instruct`. The engine prefers a repo-local materialized copy at `models/base/SmolLM2-360M-Instruct/`, while model weights remain outside Git history.

## What is implemented

- lazy-loading Transformers inference engine;
- repo-local base-model loading with controlled Hugging Face fallback;
- configurable base model and optional PEFT/LoRA adapter;
- versioned FastAPI health, model, chat and generation endpoints;
- native model chat-template prompting;
- pluggable retrieval/RAG interface;
- JSONL instruction-data normalization;
- duplicate and exact train/dev leakage checks;
- configurable LoRA or full supervised fine-tuning;
- behavioral regression evaluation;
- unit tests and GitHub Actions CI;
- architecture, training, API, data-governance and roadmap documentation.

## Structure

```text
api/                    HTTP interface
configs/                versioned training recipes
datasets/registry/      dataset provenance/status metadata
docs/                   engineering documentation
evaluation/             behavioral regression suite
models/                  model registry + local weight location
scripts/                operational utilities
silabs_ai/              core engine
training/               data and SFT pipeline
tests/                  fast tests
```

Large datasets, model weights, checkpoints and generated reports are intentionally excluded from Git.

## Quick start

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m scripts.download_base_model
python -m scripts.verify_model --load-weights
python -m scripts.preflight
uvicorn api.main:app --reload
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python -m scripts.download_base_model
python -m scripts.verify_model --load-weights
python -m scripts.preflight
uvicorn api.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

Starting the API does **not** load weights into RAM unless `SILABS_PRELOAD_MODEL=true`. On the first generation request, the engine prefers the local model directory. If it is absent and `SILABS_ALLOW_REMOTE_MODEL_DOWNLOAD=true`, it falls back to the configured Hugging Face model.

## Materialize the base model

```bash
python -m scripts.download_base_model
python -m scripts.verify_model --load-weights
```

The downloaded model lives at:

```text
models/base/SmolLM2-360M-Instruct/
```

Its identity and provenance are recorded in [models/registry.json](models/registry.json). Weight binaries are ignored by Git on purpose.

## Validate the finalized corpus

Supported migration schemas include `messages`, `instruction/output`, `prompt/response`, `question/answer` and `input/output`.

```bash
python -m training.validate_dataset datasets/processed/silabs_train.jsonl
python -m scripts.preflight --train datasets/processed/silabs_train.jsonl --dev datasets/processed/silabs_dev.jsonl
```

## Train Silabs AI v1

Review `configs/smollm2-360m-sft.yaml` and `docs/TRAINING.md` first.

```bash
python -m training.train_sft --config configs/smollm2-360m-sft.yaml
```

Training also prefers the repo-local base model. LoRA is the default. A complete training run on a 360M-parameter model should be treated as a GPU workload even though CPU execution is technically possible.

## Evaluate a model

Untouched base model:

```bash
python -m evaluation.run_eval
```

Local checkpoint or another model:

```bash
python -m evaluation.run_eval --model outputs/silabs-ai-v1
```

Reports are written under `reports/`, which is ignored by Git.

## Engineering rules

1. Product code depends on the Silabs AI API, not a particular Hugging Face class.
2. Training data gets provenance, validation, split control and license review.
3. Training loss alone never promotes a model.
4. Changing or product-specific knowledge belongs in retrieval where practical.
5. Credentials, corpora and model artifacts stay out of source control.
6. Small-model limitations are documented rather than hidden behind branding.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Training guide](docs/TRAINING.md)
- [Data governance](docs/DATA.md)
- [API](docs/API.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Roadmap](docs/ROADMAP.md)
- [Third-party components](docs/THIRD_PARTY.md)
- [Local model handling](models/README.md)

## Current milestone

**The v1 engine foundation and local-model loading path are in place.** The next milestone is reconnecting the finalized Silabs train/dev corpus, freezing its release manifest, benchmarking the untouched base model, and running a small LoRA smoke experiment before the full training run.


## One-command smoke pipeline

Once the ignored finalized corpus is present at
`datasets/processed/final_v0_1/train.jsonl` and `dev.jsonl`, run:

```bash
python -m scripts.run_smoke_pipeline
```

This performs preflight, freezes the dataset release manifest, creates the
deterministic 400/100 smoke subset, evaluates the untouched base model, runs the
LoRA smoke fine-tune, evaluates the candidate, and writes a base-vs-candidate
comparison report.

If the prepared per-dataset JSONL files are present but the finalized split
needs rebuilding first:

```bash
python -m scripts.run_smoke_pipeline --finalize
```
