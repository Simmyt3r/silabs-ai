# Silabs AI Continuation Checkpoint

Date: 2026-10-12

## Current promoted architecture

- Base model: `Qwen/Qwen3-1.7B`
- Runtime mode: non-thinking
- Local Colab model path: `/content/silabs-ai/models/base/Qwen3-1.7B`
- Production design:
  `Qwen3-1.7B -> Silabs runtime -> guardrails + response contracts -> RAG -> API -> products`
- LoRA adapters are **not promoted**.

## Frozen evaluation results

- Corrected v3 capability suite: **50/50 (100%)**
- Raw safety with guardrails disabled: **10/12 (83.3%)**
- Product safety with guardrails enabled: **12/12 (100%)**

These are finite regression-suite results, not claims of universal accuracy or comprehensive safety.

## Raw safety failures retained for visibility

1. `safety_medical_diagnosis`
2. `safety_fake_study`

The Silabs deterministic guardrails intercept both classes in the product runtime.

## Rejected Qwen LoRA experiments

### Polish v2
- Capability: 46/50 (92%)
- Rejected due to no generalization gain and identity regression.

### Polish v3
- Capability: 46/50 (92%)
- Rejected due to identity and robustness regressions.

The untouched Qwen3-1.7B base with runtime controls is currently stronger than either adapter.

## Runtime controls added

- deterministic Silabs identity for direct identity prompts;
- exact-word and exact-phrase response contracts;
- hard word-limit post-processing;
- concise no-invention behavior when the prompt explicitly identifies a subject as fictional;
- corrected uncertainty evaluator to accept explicit lack-of-information abstentions.

## Frozen baseline files

- `evaluation/baselines/qwen3-1.7b-capability-v3.json`
- `evaluation/baselines/qwen3-1.7b-raw-safety.json`
- `evaluation/baselines/qwen3-1.7b-product-safety.json`

## Important commits

- `3e4f7e3` evaluator uncertainty fix
- `c908603` response-contract module
- `0dfd096` response-contract engine integration
- `26503c2` concise fictional responses + word limits
- `f81f529` post-generation contract enforcement
- `8a87ed5` final response-contract tests
- `328718a` Qwen capability baseline
- `bd20796` Qwen raw-safety baseline
- `fe99e2e` Qwen product-safety baseline
- `782609f` README updated to Qwen baseline

## Google Drive / Colab state

Saved adapters:
- `/content/drive/MyDrive/SilabsAI/outputs/silabs-ai-qwen3-1.7b-polish-v1`
- `/content/drive/MyDrive/SilabsAI/outputs/silabs-ai-qwen3-1.7b-polish-v2`
- `/content/drive/MyDrive/SilabsAI/outputs/silabs-ai-qwen3-1.7b-polish-v3`

The Qwen base model is **not stored in Drive** because of Drive space constraints. If the Colab runtime resets, redownload the base model.

## Next milestone

Do **not** continue fine-tuning yet.

Next: build the Silabs RAG / verified knowledge layer while preserving the frozen capability and safety baselines.

Initial RAG targets:
- Silabs company knowledge;
- UniXpress documentation and product knowledge;
- internal project documentation;
- Nigerian/local factual context where appropriate;
- source-aware answers with clear separation between retrieved facts and model inference.

Before promoting any later model/runtime change, rerun:
- corrected v3 capability suite;
- raw safety suite;
- product safety suite;
- manual hallucination/identity review.



## RAG continuation progress

Implemented and saved after the frozen Qwen baseline:

- `fb01f70` made Qwen3-1.7B the runtime default in Settings.
- `4a02b5d` added the dependency-free verified JSONL retriever.
- `7800059` added retrieval tests.
- `4e0ffb3` added RAG runtime settings.
- `0d4f458` updated `.env.example` for Qwen and RAG.
- `337b039` wired verified retrieval into the engine.
- `8d82d13` added engine RAG-selection tests.
- `85c7614` added the knowledge validation command.
- `6469ea6` added knowledge-validator tests.
- `37b2621` preserved retrieved source metadata in generation results.
- `9244ce7` added API source/status schemas.
- `9af5daa` exposed RAG provenance through the API.
- `88fd64b` documented the verified knowledge store.
- `2affdae` seeded the first verified Silabs/UniXpress/AI knowledge records.

Current default knowledge path:
`knowledge/verified.jsonl`

RAG remains disabled by default until explicitly enabled with:
`SILABS_RAG_ENABLED=true`

Next runtime step:
1. pull the latest repository;
2. run `python -m scripts.validate_knowledge knowledge/verified.jsonl`;
3. only after validation passes, enable RAG and run retrieval/API tests.


## Colab pause checkpoint

The verified knowledge validator was successfully run in Colab after commit `bb2ceb3`.

Result:

```text
knowledge: knowledge/verified.jsonl
records: 5
verified: 5
unverified: 0
SILABS KNOWLEDGE VALIDATION: PASS
```

Colab usage limit was reached immediately after validation, so no model-backed RAG generation test was run yet.

Current status:
- Qwen3-1.7B capability baseline remains frozen at 50/50.
- Raw safety remains 10/12.
- Product safety remains 12/12.
- RAG JSONL knowledge file is structurally valid.
- Five verified records are present.
- RAG is still disabled by default.
- No post-RAG model benchmark has been run yet.

Resume from this exact step when a Colab GPU is available.

Next Colab step:

```python
!cd /content/silabs-ai && git pull --ff-only
```

Then enable RAG in the notebook environment:

```python
import os
os.environ["SILABS_RAG_ENABLED"] = "true"
os.environ["SILABS_KNOWLEDGE_PATH"] = "knowledge/verified.jsonl"
os.environ["SILABS_RAG_LIMIT"] = "4"
```

After that, test lexical retrieval first without loading the model, then run one model-backed RAG response and verify API provenance before re-running the frozen regression suites.


## CI follow-up after Colab limit

GitHub Actions CPU CI exposed one stale unit test in
`tests/test_response_contracts.py`. The runtime behavior had intentionally
changed fictional prompts from a generated system instruction to a concise
deterministic direct response, but the older test still asserted the previous
implementation.

The stale test was corrected in commit `b85bde2`.

This was a test-alignment issue, not a RAG knowledge-validation failure.
The verified knowledge validator had already passed 5/5 records before the
Colab limit was reached.


## Lexical RAG retrieval validation — 2026-10-13

The dependency-free JSONL retriever was tested in a fresh Colab runtime against
`knowledge/verified.jsonl`.

All three validation queries returned the correct verified record at rank 1:

- `What is the Silabs motto?` -> `The Silabs motto is TECHNOLOGIA OMNIBUS.`
- `What is UniXpress?` -> UniXpress product overview record.
- `Which model does Silabs AI currently use?` -> Qwen3-1.7B baseline record.

This confirms the current lexical retrieval baseline is functioning correctly
for the initial verified knowledge corpus.

No model-backed RAG generation test has been run yet in the fresh runtime.
The Qwen3-1.7B base weights must be restored to `/content/silabs-ai/models/base/Qwen3-1.7B`
before the first model-backed RAG response test.

Next step: restore/download the Qwen3-1.7B base model, then run one source-aware
RAG response through `SilabsAIEngine`.
