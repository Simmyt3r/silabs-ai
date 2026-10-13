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


## Fresh Colab base-model restore — 2026-10-13

A fresh Colab runtime was prepared and the Qwen3-1.7B base model was restored successfully.

Download result:

```text
Fetching 8 files: 100%
Download complete: 3.53 GB
Reconstruction complete: 4.08 GB
Silabs AI base model downloaded to:
/content/silabs-ai/models/base/Qwen3-1.7B
```

The lexical RAG baseline had already passed before this restore.

Next step:
run the model verification command with weight loading before the first
model-backed RAG response.


## Qwen weight-load verification — 2026-10-13

The freshly restored local Qwen3-1.7B base model was verified successfully in
Colab with full weight loading.

Result:

```text
Model source: models/base/Qwen3-1.7B
Architecture: qwen3
Tokenizer vocabulary: 151,669
Loading weights: 100% 311/311
Loaded weights successfully: 1,720,574,976 parameters
Silabs AI base model verification: PASS
```

This confirms the local reconstructed model is loadable and ready for the first
model-backed RAG generation test.

Next step:
enable RAG in the runtime environment and run one deterministic source-aware
chat request through `SilabsAIEngine`, printing both the answer and retrieved
source metadata.


## First successful model-backed RAG response — 2026-10-13

The first full Qwen3-1.7B + Silabs runtime + verified JSONL RAG generation test
completed successfully in Colab.

Prompt:

```text
What is the Silabs motto?
```

Answer:

```text
The Silabs motto is TECHNOLOGIA OMNIBUS.
```

Top retrieved source:

```text
silabs-internal://company/profile/2026-10-12
score: 6.461169
```

Additional lower-ranked verified context was also returned through
`GenerationResult.sources`.

Finish reason:

```text
stop
```

Validation outcome:
- answer correct;
- no invented extra fact;
- verified provenance returned successfully;
- Qwen3-1.7B local weights loaded successfully;
- RAG integration is now proven end-to-end inside `SilabsAIEngine`.

Next step:
run two additional model-backed RAG queries for UniXpress and the current Silabs
AI base model, then test the same provenance path through the HTTP API.


## Multi-query model-backed RAG validation — 2026-10-13

Two additional end-to-end RAG queries were tested successfully through the
already-loaded `SilabsAIEngine`.

### UniXpress

Prompt:

```text
What is UniXpress?
```

Answer:

```text
UniXpress is a Silabs student platform focused on organized past questions,
verified solutions, contributor rewards, and related student services.
Its slogan is Learn, Earn, Connect.
```

Top source:

```text
silabs-internal://unixpress/product-overview/2026-10-12
score: 5.246407
```

### Current Silabs AI model

Prompt:

```text
Which model does Silabs AI currently use?
```

Answer:

```text
Silabs AI currently uses Qwen3-1.7B in non-thinking mode behind the Silabs runtime.
```

Top source:

```text
silabs-internal://ai/baseline/2026-10-12
score: 5.348155
```

Validation outcome:
- correct answers;
- correct rank-1 verified source for both prompts;
- no invented extra facts;
- provenance returned in `GenerationResult.sources`;
- model-backed RAG is now validated across company, product, and AI-baseline knowledge.

Next step:
verify the same provenance path through the `/v1/chat` HTTP API without
reloading the already-loaded Qwen model.


## Second fresh-runtime Qwen restore verification — 2026-10-13

After another Colab runtime reset, the repository was recloned at commit
`d13ae2`, the lightweight/runtime dependencies were restored, and the
Qwen3-1.7B base model was downloaded again to:

```text
/content/silabs-ai/models/base/Qwen3-1.7B
```

Full verification result:

```text
Model source: models/base/Qwen3-1.7B
Architecture: qwen3
Tokenizer vocabulary: 151,669
Loading checkpoint shards: 100% 2/2
Loaded weights successfully: 1,720,574,976 parameters
Silabs AI base model verification: PASS
```

The runtime emitted a CUDA-driver warning during verification:
`Could not find cuda drivers on your machine, GPU will not be used.`

Before the next model-backed API/RAG test, explicitly check
`torch.cuda.is_available()` and the GPU name. If CUDA is unavailable, switch
the Colab runtime to a GPU rather than running Qwen3-1.7B inference on CPU.
