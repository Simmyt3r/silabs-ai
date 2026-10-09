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


## Current engine baselines

After separating deterministic guardrails from a shorter model-facing system
prompt, the untouched base model now has two current capability references:

- compact 20-case suite: **19/20 (95%)**;
- extended 50-case suite v1: **40/50 (80%)**.

The concise prompt fixed the compact suite's strict-format failures without
weakening the deterministic guardrail layer.

Safety is intentionally reported in two layers:

- engine-level runtime guardrails: **12/12 (100%)** on the configured
  safety/uncertainty regression suite;
- raw model with runtime guardrails disabled: **4/12 (33.3%)**.

The raw score makes the architectural decision explicit: deterministic
guardrails are currently mandatory for product use. They are not evidence that
the underlying 360M model is intrinsically safe.

## Commercial 400/100 smoke: historical pass, not promoted

Workflow run: `37884408454`

The conservative commercial-profile recipe used q/v LoRA targets, rank 8,
alpha 16, a 5e-5 learning rate and one epoch over a 400/100 smoke subset.

Under the engine state that launched the run:

- baseline: **70%** on 50 cases;
- candidate: **72%**;
- delta: **+2 percentage points**;
- regressions: **0**;
- historical promotion gate: **PASS**.

During the long CPU run, the base-engine prompt architecture improved
independently and established a newer **80%** 50-case baseline. Therefore the
72% candidate is not promoted from the historical result. Its saved adapter is
being reevaluated under the current engine and raw-safety gates before a final
decision.

The forward capability suite is `evaluation/cases_extended_v2.jsonl`, which
corrects two evaluator-only quirks while preserving the genuine behavioral
failures.


## Alignment smoke: infrastructure timeout, retry active

Workflow run: `37891192542`

The first balanced-alignment run successfully rebuilt the commercially screened
corpus, produced an exactly balanced 180-record public training subset
(30 records from each of ARC Challenge, ARC Easy, GSM8K, HotpotQA, OASST1 and
OpenMathInstruct-2), added 45 benchmark-disjoint Silabs alignment records,
created a 60-record balanced dev set, and passed preflight with zero train/dev
overlap and zero evaluation-prompt leakage.

The LoRA training step was cancelled by the workflow's 75-minute job timeout.
This is recorded as an infrastructure timeout, not a model-quality failure.

The workflow is now split into two jobs:

1. preparation and base baselines, with its own 45-minute budget;
2. training, candidate evaluation and promotion gates, with a fresh 120-minute
   budget.

The training data and baseline reports are transferred between jobs as a
GitHub Actions artifact so the experiment itself remains unchanged.
