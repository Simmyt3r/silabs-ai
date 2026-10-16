# Silabs Humanizer

Silabs Humanizer is a completely offline desktop writing and document-editing product built on Silabs AI.

## Product promise

Silabs Humanizer improves writing without silently changing facts.

## v0.1 scope

- Open DOCX, TXT and Markdown documents
- Edit selected text
- Humanize writing
- Improve grammar
- Academic rewrite
- Simplify
- Shorten
- Expand
- Preserve citations, numbers, URLs, dates and other protected content
- Compare original and revised text
- Accept or reject changes
- Save/export DOCX
- Run inference completely offline

## Architecture

The product reuses the common Silabs AI intelligence layer while keeping product-specific document parsing, preservation, rewriting, criticism and UI logic here.

See [architecture.md](architecture.md) and [ROADMAP.md](ROADMAP.md).


## Current implementation (engineering preview)

The repository contains a working code path for local DOCX import, conservative
rewrite, and export. It is **not** a production desktop application yet.

Supported import: .docx, .txt, .md. The pilot rewrite CLI currently exports
only .docx. Safe rewrites are limited to simple single-run body paragraphs;
headings and complex formatting are deliberately skipped. Tables are opt-in.

### Install (development)

From the repository root:

```bash
python -m pip install -r products/humanizer/requirements.txt
# Only for GGUF local inference; install a compatible llama-cpp-python build
# for your CPU/GPU separately.
```

Use a **local** Qwen3-1.7B GGUF file. Nothing is downloaded automatically.

### Run a 3-paragraph offline pilot

```bash
python -m products.humanizer.service.cli \
  --input ./sample.docx \
  --output ./sample-humanized.docx \
  --backend gguf \
  --model ./models/qwen3-1.7b-q4.gguf \
  --mode academic \
  --limit 3
```

Alternative for existing local Transformers model weights:

```bash
python -m pip install -r requirements.txt
python -m products.humanizer.service.cli \
  --input ./sample.docx \
  --output ./sample-humanized.docx \
  --backend transformers \
  --model ./models/base/Qwen3-1.7B \
  --mode natural \
  --limit 1
```

The Transformers backend refuses missing local weights and disables remote
model download; using CPU may be slow. The GGUF backend is recommended for
eventual consumer desktop distribution.

### Regression tests

```bash
python -m pytest products/humanizer/tests -q
```

**Important:** Tests use fixtures and fake text generation. They do **not** prove
that a real Qwen response preserves facts or reads naturally. Real-device
quality evaluation and a reviewed desktop UI are separate release gates.

The product must never present an automatically revised document as verified.
Review text and citations before accepting changes.

### Test with actual Qwen3 local weights

```bash
python -m products.humanizer.service.smoke --backend gguf --model ./models/qwen3-1.7b-q4.gguf
# Or, if local Transformers weights already exist:
python -m products.humanizer.service.smoke --backend transformers --model ./models/base/Qwen3-1.7B --device cpu
```

The smoke command reports PASS/FAIL for protected tokens and DOCX round-trip. It does **not** replace manual assessment of naturalness or factual accuracy.
