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

