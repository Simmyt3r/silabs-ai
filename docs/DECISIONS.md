# Architecture Decision Log

## ADR-001: Fine-tune a pretrained model for v1

**Status: Accepted**

Silabs AI v1 uses a pretrained open-weight language model as its foundation instead of continuing the tiny from-scratch model as the production path. The scratch model remains useful for research and learning.

## ADR-002: SmolLM2-360M-Instruct is the first base

**Status: Accepted for v1 experiments**

Model ID: `HuggingFaceTB/SmolLM2-360M-Instruct`.

It is small enough for comparatively accessible experimentation while already providing pretrained instruction-following capability. The engine remains model-agnostic so this decision can be revised.

## ADR-003: LoRA first

**Status: Accepted**

The initial recipe uses PEFT/LoRA. Full fine-tuning remains possible but is not the default.

## ADR-004: Retrieval is separate from fine-tuning

**Status: Accepted**

Fine-tuning should primarily improve durable behavior and capability. Frequently changing knowledge belongs in retrieval where practical.

## ADR-005: No datasets or weights in Git

**Status: Accepted**

Git holds code, manifests and documentation. Training corpora, weights, checkpoints and runtime indexes remain outside version control.

## ADR-006: Stable API before product integrations

**Status: Accepted**

Silabs products call a versioned Silabs AI API rather than depending directly on Transformers internals. This lets us replace or route models without coordinated rewrites across every product.
