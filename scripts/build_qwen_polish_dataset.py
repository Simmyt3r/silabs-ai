from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from silabs_ai.config import Settings


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def load_records(path: Path, dataset_name: str) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} must contain a non-empty records list")

    output: list[dict] = []
    system_prompt = Settings().system_prompt

    for index, row in enumerate(records, start=1):
        required = ["task", "domain", "instruction", "input", "output"]
        if not isinstance(row, dict) or not all(str(row.get(k) or "").strip() for k in required):
            raise ValueError(f"{path}: incomplete record {index}")

        digest = hashlib.sha256(
            f"{row['task']}\n{normalize(row['input'])}\n{normalize(row['output'])}".encode("utf-8")
        ).hexdigest()[:20]

        output.append({
            "id": f"{dataset_name}_{digest}",
            "dataset": dataset_name,
            "task": str(row["task"]).strip(),
            "domain": str(row["domain"]).strip(),
            "system": system_prompt,
            "instruction": str(row["instruction"]).strip(),
            "input": str(row["input"]).strip(),
            "output": str(row["output"]).strip(),
            "metadata": {
                "source": dataset_name,
                "curated": True,
                "benchmark_disjoint_required": True,
            },
        })
    return output


def load_eval_prompts(paths: list[Path]) -> dict[str, str]:
    prompts: dict[str, str] = {}
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                prompt = str(row.get("prompt") or "").strip()
                if prompt:
                    prompts[normalize(prompt)] = f"{path}:{line_number}:{row.get('id', '<unknown>')}"
    return prompts


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the small benchmark-disjoint Qwen polish train/dev dataset."
    )
    parser.add_argument(
        "--train-curated",
        type=Path,
        default=Path("datasets/curated/qwen_polish_v1.json"),
    )
    parser.add_argument(
        "--dev-curated",
        type=Path,
        default=Path("datasets/curated/qwen_polish_dev_v1.json"),
    )
    parser.add_argument(
        "--eval-cases",
        type=Path,
        action="append",
        default=[],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets/processed/qwen_polish"),
    )
    args = parser.parse_args()

    eval_paths = args.eval_cases or [
        Path("evaluation/cases_extended_v3.jsonl"),
        Path("evaluation/cases_safety.jsonl"),
    ]
    eval_prompts = load_eval_prompts(eval_paths)

    train = load_records(args.train_curated, "silabs_qwen_polish_v1")
    dev = load_records(args.dev_curated, "silabs_qwen_polish_dev_v1")

    train_inputs = {normalize(row["input"]): row["id"] for row in train}
    dev_inputs = {normalize(row["input"]): row["id"] for row in dev}

    overlap = sorted(set(train_inputs) & set(dev_inputs))
    if overlap:
        raise ValueError(f"Train/dev prompt overlap detected: {overlap[0]}")

    for split_name, rows in (("train", train), ("dev", dev)):
        seen: set[str] = set()
        for row in rows:
            key = normalize(row["input"])
            if key in seen:
                raise ValueError(f"Duplicate {split_name} prompt: {row['input']}")
            seen.add(key)
            if key in eval_prompts:
                raise ValueError(
                    f"{split_name}/evaluation leakage: {row['id']} matches {eval_prompts[key]}"
                )

    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "dev.jsonl", dev)

    manifest = {
        "schema_version": 1,
        "strategy": "small curated Qwen polish train/dev with benchmark leakage checks",
        "train_records": len(train),
        "dev_records": len(dev),
        "evaluation_files_checked": [str(path) for path in eval_paths],
        "evaluation_prompt_leakage": 0,
        "train_dev_overlap": 0,
        "train_path": str(args.output_dir / "train.jsonl"),
        "dev_path": str(args.output_dir / "dev.jsonl"),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print("QWEN POLISH DATASET PASS")
    print(f"train: {len(train)}")
    print(f"dev: {len(dev)}")
    print("evaluation prompt leakage: 0")
    print("train/dev overlap: 0")
    print(f"manifest: {args.output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
