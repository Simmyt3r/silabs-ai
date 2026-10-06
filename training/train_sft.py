from __future__ import annotations

import argparse
from pathlib import Path

import torch
import yaml
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

from .data import load_messages


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("training config must be a YAML mapping")
    return config


def render_dataset(path: str, tokenizer) -> Dataset:
    rows = load_messages(path)
    texts = [
        tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        for messages in rows
    ]
    return Dataset.from_dict({"text": texts})


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Silabs AI")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/smollm2-360m-sft.yaml"),
    )
    args = parser.parse_args()
    cfg = load_config(args.config)

    model_id = cfg["model"]["id"]
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype_name = cfg["model"].get("dtype", "auto")
    dtype_map = {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "auto": "auto",
    }
    if dtype_name not in dtype_map:
        raise ValueError(f"Unsupported dtype: {dtype_name}")

    model_kwargs = {"torch_dtype": dtype_map[dtype_name]}
    if cfg["model"].get("device_map", "auto") == "auto":
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
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
                    "q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                ],
            ),
        )
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

    train_data = render_dataset(cfg["data"]["train"], tokenizer)
    eval_data = render_dataset(cfg["data"]["dev"], tokenizer)
    max_length = int(cfg["data"].get("max_length", 1024))

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_length,
            padding=False,
        )

    train_data = train_data.map(tokenize, batched=True, remove_columns=["text"])
    eval_data = eval_data.map(tokenize, batched=True, remove_columns=["text"])

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
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    trainer.train()
    trainer.save_model(training["output_dir"])
    tokenizer.save_pretrained(training["output_dir"])
    print(f"Saved Silabs AI checkpoint to {training['output_dir']}")


if __name__ == "__main__":
    main()
