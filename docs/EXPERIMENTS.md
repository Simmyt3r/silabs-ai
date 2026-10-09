# Silabs AI Experiment History

This document records model-training experiments that materially changed the
project's understanding of the training recipe. Raw workflow reports remain the
source of truth; this file is the human-readable decision log.

## Untouched base

Model: `HuggingFaceTB/SmolLM2-360M-Instruct`

The original 20-case deterministic suite scored **18/20 (90%)**. The main
visible weakness was strict output-format compliance.

## Fast smoke: promising

Workflow run: `37622774290`

- research profile;
- 100 selected train records / 25 dev records;
- LoRA rank 8, alpha 16;
- q/k/v/o projection targets;
- one epoch;
- 1,638,400 trainable parameters;
- training loss: 1.2130;
- baseline: 90%;
- candidate: **95%**;
- improvements: 1;
- regressions: 0.

The adapter fixed the three-primary-colors formatting case. This experiment
proved that Silabs SFT can improve the base model without immediate regression,
but its sample size is too small for release promotion.

Machine-readable record:
`experiments/2026-10-07-fast-smoke.json`.

## Two-step CI smoke: infrastructure validation

Workflow run: `37624357466`

A deliberately tiny training run verified the complete
train -> save adapter -> reload -> evaluate path. It remained at 90% and was
not intended as a quality experiment.

## Extended 400-example research smoke: rejected

Workflow run: `37681413546`

- research profile;
- 400 train / 100 dev selected records;
- one epoch;
- learning rate: 2e-4;
- 1,638,400 trainable parameters;
- training loss: 1.2927;
- eval loss: 1.3733;
- baseline: 90%;
- candidate: **85%**;
- improvements: 1;
- regressions: 2.

Regressions appeared on a simple subtraction word problem and a transitive
ordering problem. The promotion safety gate rejected the checkpoint.

This experiment strongly suggests that the 400-example recipe adapted too
aggressively at the chosen learning rate. More data did not automatically
produce a better model. The adapter must not be used for product integration.

Machine-readable record:
`experiments/2026-10-07-extended-smoke-400-rejected.json`.

## Current experiment: conservative commercial smoke

The next experiment uses the commercially screened corpus, 400/100 records,
a lower learning rate of 5e-5, and only q/v LoRA projection targets. Evaluation
uses the expanded 50-case suite and the reusable zero-regression promotion
gate.

A candidate is not promoted merely for lowering training loss. It must match or
beat the untouched base-model score and introduce zero behavioral regressions
on the configured gate.


## Runtime guardrail baseline: 12/12

Workflow run: `37885716389`

The deterministic pre-generation guardrail layer passed all 12 configured
privacy, malicious-cyber, medical, financial, legal and epistemic regression
cases. All intercepted cases completed before model inference.

This result is an **engine-level regression milestone**, not a statement that
the raw 360M model is comprehensively safe. Raw-model safety evaluation with
guardrails disabled and manual review remain required before release.
