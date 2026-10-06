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

## Accepted data format

Preferred canonical JSONL record:

```json
{"messages":[{"role":"user","content":"What is 2 + 3?"},{"role":"assistant","content":"2 + 3 = 5."}]}
```

Migration formats are also accepted:

```json
{"instruction":"What is 2 + 3?","output":"2 + 3 = 5."}
{"prompt":"What is 2 + 3?","response":"2 + 3 = 5."}
{"question":"What is 2 + 3?","answer":"2 + 3 = 5."}
```

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
