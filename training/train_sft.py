from __future__ import annotations

import argparse
from pathlib import Path

import torch
import yaml
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

from silabs_ai.model_source import resolve_model_source
from .data import load_messages


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("training config must be a YAML mapping")
    return config


def build_tokenized_dataset(path: str, tokenizer, max_length: int) -> Dataset:
    """Build causal-LM examples while masking prompt tokens from the loss."""
    rows = load_messages(path)
    examples: list[dict[str, list[int]]] = []
    skipped = 0

    for messages in rows:
        if not messages or messages[-1]["role"] != "assistant":
            skipped += 1
            continue

        full_ids = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=False,
        )
        prompt_ids = tokenizer.apply_chat_template(
            messages[:-1],
            tokenize=True,
            add_generation_prompt=True,
        )

        full_ids = list(full_ids[:max_length])
        prompt_length = min(len(prompt_ids), len(full_ids))
        labels = full_ids.copy()
        labels[:prompt_length] = [-100] * prompt_length

        if not full_ids or all(label == -100 for label in labels):
            skipped += 1
            continue

        examples.append({
            "input_ids": full_ids,
            "attention_mask": [1] * len(full_ids),
            "labels": labels,
        })

    if not examples:
        raise ValueError(f"No trainable examples remain after tokenization: {path}")
    if skipped:
        print(f"Skipped {skipped} records with no trainable assistant tokens from {path}")

    return Dataset.from_list(examples)


class CausalLMCollator:
    """Pad input tensors and preserve -100 label masking."""

    def __init__(self, tokenizer) -> None:
        self.tokenizer = tokenizer

    def __call__(self, features: list[dict]) -> dict[str, torch.Tensor]:
        input_features = [
            {
                "input_ids": feature["input_ids"],
                "attention_mask": feature["attention_mask"],
            }
            for feature in features
        ]
        batch = self.tokenizer.pad(input_features, padding=True, return_tensors="pt")

        max_length = batch["input_ids"].shape[1]
        labels = torch.full(
            (len(features), max_length),
            -100,
            dtype=torch.long,
        )

        for row, feature in enumerate(features):
            values = torch.tensor(feature["labels"], dtype=torch.long)
            if self.tokenizer.padding_side == "left":
                labels[row, -len(values) :] = values
            else:
                labels[row, : len(values)] = values

        batch["labels"] = labels
        return batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Silabs AI")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/smollm2-360m-sft.yaml"),
    )
    args = parser.parse_args()
    cfg = load_config(args.config)

    model_cfg = cfg["model"]
    source = resolve_model_source(
        local_path=model_cfg.get("local_path"),
        remote_id=model_cfg["id"],
        allow_remote=bool(model_cfg.get("allow_remote", True)),
    )
    source_kwargs = {"local_files_only": source.is_local}

    tokenizer = AutoTokenizer.from_pretrained(source.value, **source_kwargs)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype_name = model_cfg.get("dtype", "auto")
    dtype_map = {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "auto": "auto",
    }
    if dtype_name not in dtype_map:
        raise ValueError(f"Unsupported dtype: {dtype_name}")

    model_kwargs = {
        "torch_dtype": dtype_map[dtype_name],
        **source_kwargs,
    }
    if model_cfg.get("device_map") == "auto":
        model_kwargs["device_map"] = "auto"

    print(
        "Loading training base model from "
        f"{source.value} ({'local' if source.is_local else 'remote'})"
    )
    model = AutoModelForCausalLM.from_pretrained(source.value, **model_kwargs)
    model.config.use_cache = False

    lora_cfg = cfg.get("lora", {})
    if lora_cfg.get("enabled", True):
        peft_config = LoraConfig(
            r=int(lora_cfg.get("r", 16)),
            lora_alpha=int(lora_cfg.get("alpha", 32)),
            lora_dropout=float(lora_cfg.get("dropout", 0.05)),
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=lora_cfg.get(
                "target_modules",
                [
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ],
            ),
        )
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

    max_length = int(cfg["data"].get("max_length", 1024))
    train_data = build_tokenized_dataset(cfg["data"]["train"], tokenizer, max_length)
    eval_data = build_tokenized_dataset(cfg["data"]["dev"], tokenizer, max_length)

    training = cfg["training"]
    training_args = TrainingArguments(
        output_dir=training["output_dir"],
        num_train_epochs=float(training.get("epochs", 2)),
        per_device_train_batch_size=int(training.get("batch_size", 1)),
        per_device_eval_batch_size=int(training.get("eval_batch_size", 1)),
        gradient_accumulation_steps=int(training.get("gradient_accumulation_steps", 16)),
        learning_rate=float(training.get("learning_rate", 2e-4)),
        warmup_ratio=float(training.get("warmup_ratio", 0.03)),
        weight_decay=float(training.get("weight_decay", 0.01)),
        logging_steps=int(training.get("logging_steps", 10)),
        eval_strategy="steps",
        eval_steps=int(training.get("eval_steps", 200)),
        save_steps=int(training.get("save_steps", 200)),
        save_total_limit=int(training.get("save_total_limit", 2)),
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=bool(training.get("fp16", False)),
        bf16=bool(training.get("bf16", False)),
        gradient_checkpointing=bool(training.get("gradient_checkpointing", True)),
        report_to=training.get("report_to", "none"),
        seed=int(training.get("seed", 42)),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=eval_data,
        data_collator=CausalLMCollator(tokenizer),
    )

    trainer.train()
    trainer.save_model(training["output_dir"])
    tokenizer.save_pretrained(training["output_dir"])
    print(f"Saved Silabs AI checkpoint to {training['output_dir']}")


if __name__ == "__main__":
    main()
