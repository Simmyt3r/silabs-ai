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


## Large corpus expansion

The tracked `knowledge/verified.jsonl` file remains the small, reviewed seed
corpus. Large generated knowledge is intentionally written under
`knowledge/generated/`, which is ignored by Git.

The approved source registry is:

```text
knowledge/source_registry.json
```

It currently includes:
- first-party documentation from the repositories registered under
  `Simmyt3r/*`;
- official Nigerian government and education sources;
- official documentation for infrastructure and services used by Silabs
  projects.

Build the expanded corpus with:

```bash
python -m scripts.build_expanded_knowledge
```

Output:

```text
knowledge/generated/verified.jsonl
knowledge/generated/manifest.json
```

Validate it with:

```bash
python -m scripts.validate_knowledge knowledge/generated/verified.jsonl
```

Then point the runtime at it:

```text
SILABS_RAG_ENABLED=true
SILABS_KNOWLEDGE_PATH=knowledge/generated/verified.jsonl
```

For a quick smoke build before downloading every registered repository:

```bash
python -m scripts.build_expanded_knowledge --max-repos 3 --max-web-pages 5
```

If a registered GitHub repository is private, expose a `GITHUB_TOKEN` to the
runtime environment through a secret manager or Colab secret. Do not place the
token in the repository or knowledge corpus.

## Trust versus licensing

`verified=true` means the source is approved as authoritative enough for the
knowledge layer. It is not a legal determination that third-party text can be
republished.

First-party repository material and externally published official documentation
remain subject to their respective ownership, licenses and terms. Generated
bulk corpus files are therefore kept local and out of Git by default.

When external material is later packaged, redistributed or used for training
rather than retrieval, perform a separate license review.
