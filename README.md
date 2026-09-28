# Silabs AI v0.1

Zero-cost-first academic AI scaffold for Silabs/UniXpress. It separates immutable raw data, processed training data, proprietary PQ data, RAG, model inference, and evaluation.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest -q
uvicorn api.main:app --reload
```

Health: `GET /v1/health`. Chat: `POST /v1/chat` with `{"message":"Explain recursion simply"}`. The first chat call downloads the configured open-weight model, so local CPU use may be slow.

## Dataset layout
- `datasets/raw/`: immutable originals; intentionally gitignored.
- `datasets/processed/`: unified JSONL training records.
- `datasets/evaluation/`: evaluation-only data such as MMLU-Pro.
- `datasets/registry/datasets.json`: provenance/licensing registry.
- `pq/images/`: original PQ scans; intentionally gitignored.

## Prepare public datasets
```bash
python -m training.prepare_dataset gsm8k
python -m training.prepare_dataset arc_easy
python -m training.prepare_dataset arc_challenge
python -m training.prepare_dataset sciq
python -m training.prepare_dataset openbookqa
python -m training.validate_dataset datasets/processed/gsm8k.jsonl
```

## Audit the 52K AI/Human CSV
Expected columns: `text,label`.
```bash
python scripts/audit_ai_human.py path/to/AI_Human.csv
```

This corpus is for classification research/auditing, not a paired rewriting corpus and not for optimizing detector evasion.

## PQ pipeline status
The PQ schema and storage layout are included. OCR/vision extraction is intentionally a later phase because image extraction must be reviewed against originals before records become GOLD.

## Licensing
Registry entries marked `REVIEW_REQUIRED` must be verified against the current source dataset card/license before commercial training. Public availability is not permission by magic.
