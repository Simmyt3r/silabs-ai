# Training Silabs AI

## Goal

Silabs AI v1 fine-tunes a pretrained open-weight model instead of using the previous tiny from-scratch model as the production path. The scratch-model work remains useful research, but useful language pretraining from zero requires much more compute and data than the current project should spend.

## Base model

Default model ID:

```text
HuggingFaceTB/SmolLM2-360M-Instruct
```

The engine and training configuration are designed so this can be replaced later.

## Why LoRA first

Full fine-tuning updates every parameter and requires substantially more memory for parameters, gradients and optimizer state. LoRA trains a small set of adapter weights on top of the pretrained model, making iteration more practical.

For the first serious run:

1. keep LoRA enabled;
2. begin at sequence length 1024;
3. use batch size 1 plus gradient accumulation;
4. run a tiny smoke dataset before the complete corpus;
5. save checkpoints regularly;
6. evaluate the untouched base model before comparing a trained candidate.

CPU execution exists as a code path, but a complete 360M-parameter training run is realistically a GPU workload.

## Finalized Silabs corpus schema

The existing finalized Silabs data uses these top-level fields:

```text
id, dataset, task, domain, instruction, input, output, metadata
```

The trainer intentionally preserves **both** `instruction` and `input`. This matters because some records use a general instruction while the actual user question is stored in `input`.

Example:

```json
{
  "id": "example_001",
  "dataset": "source-name",
  "task": "conversation",
  "domain": "general",
  "instruction": "Respond helpfully and accurately to the user.",
  "input": "What is 2 + 3?",
  "output": "5",
  "metadata": {"split": "train"}
}
```

The loader also accepts role/content `messages`, prompt/response and question/answer records for future or imported datasets.

## Preflight

```bash
python -m scripts.preflight --train datasets/processed/silabs_train.jsonl --dev datasets/processed/silabs_dev.jsonl
```

This verifies parsing, record structure, duplicate statistics and exact overlap between train and dev splits while reporting the active Python, PyTorch, Transformers and CUDA environment.

It does not replace source-license review, semantic-duplicate review, benchmark-contamination checks, or human answer-quality review.

## Smoke run

Never begin by feeding the complete corpus to a new training configuration. First create a small temporary train/dev subset and verify that:

- chat-template rendering succeeds;
- tokenization succeeds;
- loss is finite;
- checkpoint saving succeeds;
- the checkpoint can be loaded by the inference engine;
- behavioral evaluation runs end-to-end.

## Start SFT

Edit `configs/smollm2-360m-sft.yaml`, then run:

```bash
python -m training.train_sft --config configs/smollm2-360m-sft.yaml
```

## Promotion gate

A checkpoint is not promoted merely because training reached the final step. Promotion should require:

1. dataset preflight pass;
2. no known train/dev leakage;
3. behavior score at least competitive with the untouched base model;
4. manual conversation review;
5. math/reasoning spot checks;
6. repetition and degeneration review;
7. safety behavior review;
8. recorded model config, dataset release and evaluation report.

## Adapters and deployment

Keep LoRA adapters separate while experimenting. A selected release can later be merged into a base model or served as base-plus-adapter. Do not commit either model weights or adapters to Git.


## Rebuild and freeze the finalized corpus

The canonical Silabs data finalizer is preserved in the repository:

```bash
python -m scripts.finalize_training_data_v1_2
```

It rebuilds the final train/dev split from the prepared per-dataset JSONL files,
groups by normalized input across all datasets, and refuses to write a split if
the same normalized input crosses train and dev.

After the final split exists, freeze its exact hashes, distributions and
deterministic smoke subset:

```bash
python -m scripts.freeze_dataset_release \
  --train datasets/processed/final_v0_1/train.jsonl \
  --dev datasets/processed/final_v0_1/dev.jsonl \
  --name silabs-v1
```

This creates a tracked release manifest under `datasets/registry/releases/`
and local ignored smoke files under `datasets/processed/smoke/`.

Run the smoke recipe before the full configuration:

```bash
python -m training.train_sft --config configs/smollm2-360m-smoke.yaml
python -m evaluation.run_eval \
  --model outputs/silabs-ai-v1-smoke \
  --offline \
  --report-name smoke_candidate.json
```
