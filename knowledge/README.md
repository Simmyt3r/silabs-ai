# Silabs AI Verified Knowledge

This directory contains the small, source-aware knowledge layer used by the
offline JSONL RAG baseline.

## Runtime file

`verified.jsonl` is the default knowledge file when:

```text
SILABS_RAG_ENABLED=true
SILABS_KNOWLEDGE_PATH=knowledge/verified.jsonl
```

RAG is disabled by default.

## Record format

One JSON object per line:

```json
{
  "title": "Human-readable subject",
  "text": "A concise factual passage suitable for retrieval.",
  "source": "silabs-internal://source-or-document-id",
  "verified": true
}
```

Required fields:

- `text`: the factual content retrieved into model context.
- `source`: provenance identifier. Never use an empty or placeholder source.

Optional fields:

- `title`: improves lexical retrieval and human review.
- `verified`: defaults to `true`. The production retriever ignores records
  explicitly marked `false`.

Additional metadata fields may be stored for future tooling, but the current
baseline retriever only consumes the fields above.

## Verification rule

A record may be marked verified only when it comes from a source the Silabs
team accepts as authoritative for that fact, such as:

- an approved internal company record;
- an official product specification;
- a controlled project document;
- a primary external source reviewed by the team.

Do not convert model-generated guesses, chat summaries, or unsourced internet
claims into verified records.

Changing information should be updated in RAG rather than fine-tuned into the
base model.

## Validate before use

```bash
python -m scripts.validate_knowledge knowledge/verified.jsonl
```

A passing validator checks JSON structure, required provenance, counts verified
and unverified records, and warns about duplicate text.

## Design boundary

This JSONL retriever is the deterministic offline baseline. A later semantic or
vector retriever should implement the existing `Retriever` protocol so the AI
engine and API do not need to change.

The frozen Qwen3-1.7B capability and safety suites must be rerun before a RAG
change is promoted to production.
