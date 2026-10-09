# Silabs AI Architecture

## Purpose

Silabs AI is the shared intelligence layer for Silabs products. Product applications should depend on a stable Silabs API instead of importing a particular model library directly.

```text
Silabs products
      |
      v
Silabs AI API
      |
      +----> Retrieval / RAG
      |
      v
Inference engine
      |
      v
Base model + optional Silabs adapter
```

## Core engine

`silabs_ai.engine.SilabsAIEngine` owns tokenizer/model lifecycle and generation. Loading is lazy so health checks and API startup do not trigger a model download.

Model identity is configuration. Product code must not depend on the first base model being permanent.

## Model strategy

The first supported base is `HuggingFaceTB/SmolLM2-360M-Instruct`. A LoRA adapter can be selected with `SILABS_ADAPTER_PATH`; a merged or replacement checkpoint can be selected with `SILABS_MODEL_ID`.

## Retrieval strategy

`Retriever` is a protocol and `NullRetriever` is the default implementation. A future pgvector, local vector index, search service, or product-specific retriever can implement the same interface.

Changing company facts, private product information, current university data, and user-specific context should generally be retrieved at inference time instead of repeatedly written into model weights.

## API boundary

Initial versioned routes:

- `GET /v1/health`
- `GET /v1/model`
- `POST /v1/chat`
- `POST /v1/generate`

Breaking request/response changes should receive a new API version instead of silently breaking every Silabs product.

## Training flow

```text
source datasets
  -> cleaned/finalized JSONL
  -> normalization + validation + leakage checks
  -> model chat template
  -> tokenization
  -> SFT / LoRA
  -> candidate checkpoint
  -> behavioral + manual evaluation
  -> promoted release
```

## Evaluation

Training loss is not a product-quality metric. The behavioral harness is kept separate and should grow to cover instruction following, conversation, reasoning, repetition, safety, domain tasks, and regressions observed in real use.

## Deployment direction

Development uses Transformers directly. Production can later add a dedicated inference server, streaming, batching, quantization, model routing, caching, authentication, quotas and observability behind the same API contract.


## Runtime behavior contract

Silabs AI uses two layers instead of forcing a small model to carry every rule
inside one oversized system prompt.

The default system prompt establishes identity, precise instruction following,
brevity when requested, factual accuracy, and uncertainty instead of
fabrication.

`silabs_ai.guardrails.BasicGuardrail` handles narrow high-risk classes before
retrieval or model inference, including credentials/private PII, malicious
phishing/malware/ransomware requests, urgent medical escalation, diagnosis
certainty, guaranteed financial/legal outcomes, forced false claims and exact
future certainty.

This separation keeps the model prompt shorter while making critical behavior
deterministic. Model adapters are still evaluated independently and are not
allowed to regress capability or raw-model safety during promotion.
