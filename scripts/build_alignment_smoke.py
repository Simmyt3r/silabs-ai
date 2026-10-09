from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from training.data import iter_jsonl


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def read_eval_prompts(paths: list[Path]) -> dict[str, str]:
    prompts: dict[str, str] = {}
    for path in paths:
        for line_number, row in iter_jsonl(path):
            prompt = str(row.get("prompt") or "").strip()
            if not prompt:
                raise ValueError(f"Missing prompt in {path}:{line_number}")
            key = normalize(prompt)
            prompts[key] = f"{path}:{line_number}:{row.get('id', '<unknown>')}"
    return prompts


def read_curated(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} must contain a non-empty records list")

    output: list[dict] = []
    for index, row in enumerate(records, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{path}: record {index} must be an object")
        input_text = str(row.get("input") or "").strip()
        answer = str(row.get("output") or "").strip()
        instruction = str(row.get("instruction") or "").strip()
        task = str(row.get("task") or "").strip()
        domain = str(row.get("domain") or "").strip()
        if not all([input_text, answer, instruction, task, domain]):
            raise ValueError(f"{path}: incomplete record {index}")

        digest = hashlib.sha256(
            f"{task}\n{normalize(input_text)}\n{normalize(answer)}".encode("utf-8")
        ).hexdigest()[:20]

        output.append(
            {
                "id": f"silabs_alignment_v1_{digest}",
                "dataset": "silabs_alignment_v1",
                "task": task,
                "domain": domain,
                "instruction": instruction,
                "input": input_text,
                "output": answer,
                "metadata": {
                    "source": "Silabs curated alignment v1",
                    "curated": True,
                    "benchmark_disjoint_required": True,
                },
            }
        )
    return output


def load_jsonl(path: Path) -> list[dict]:
    return [row for _, row in iter_jsonl(path)]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge balanced public smoke data with leakage-checked Silabs alignment data"
    )
    parser.add_argument(
        "--public-train",
        type=Path,
        default=Path("datasets/processed/smoke_balanced/train.jsonl"),
    )
    parser.add_argument(
        "--public-dev",
        type=Path,
        default=Path("datasets/processed/smoke_balanced/dev.jsonl"),
    )
    parser.add_argument(
        "--curated",
        type=Path,
        default=Path("datasets/curated/alignment_v1.json"),
    )
    parser.add_argument(
        "--eval-cases",
        type=Path,
        action="append",
        default=[],
        help="Evaluation JSONL files whose prompts must never appear in curated training data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets/processed/smoke_alignment"),
    )
    args = parser.parse_args()

    eval_paths = args.eval_cases or [
        Path("evaluation/cases_extended_v2.jsonl"),
        Path("evaluation/cases_safety.jsonl"),
    ]
    eval_prompts = read_eval_prompts(eval_paths)

    public_train = load_jsonl(args.public_train)
    public_dev = load_jsonl(args.public_dev)
    curated = read_curated(args.curated)

    public_train_inputs = {
        normalize(row.get("input", "")): row.get("id", "<unknown>")
        for row in public_train
        if str(row.get("input") or "").strip()
    }
    public_dev_inputs = {
        normalize(row.get("input", "")): row.get("id", "<unknown>")
        for row in public_dev
        if str(row.get("input") or "").strip()
    }

    seen_curated: set[str] = set()
    for row in curated:
        key = normalize(row["input"])
        if key in eval_prompts:
            raise ValueError(
                "Curated/evaluation prompt leakage detected: "
                f"{row['id']} matches {eval_prompts[key]}"
            )
        if key in public_dev_inputs:
            raise ValueError(
                "Curated prompt overlaps public dev split: "
                f"{row['id']} matches {public_dev_inputs[key]}"
            )
        if key in public_train_inputs:
            raise ValueError(
                "Curated prompt duplicates public train split: "
                f"{row['id']} matches {public_train_inputs[key]}"
            )
        if key in seen_curated:
            raise ValueError(f"Duplicate curated input: {row['input']}")
        seen_curated.add(key)

    train_rows = public_train + curated
    dev_rows = public_dev

    train_path = args.output_dir / "train.jsonl"
    dev_path = args.output_dir / "dev.jsonl"
    write_jsonl(train_path, train_rows)
    write_jsonl(dev_path, dev_rows)

    domains = Counter(row["domain"] for row in curated)
    tasks = Counter(row["task"] for row in curated)
    manifest = {
        "schema_version": 1,
        "strategy": "balanced public smoke + benchmark-disjoint Silabs curated alignment",
        "public_train_records": len(public_train),
        "curated_train_records": len(curated),
        "final_train_records": len(train_rows),
        "dev_records": len(dev_rows),
        "evaluation_files_checked": [str(path) for path in eval_paths],
        "evaluation_prompt_leakage": 0,
        "public_dev_prompt_overlap": 0,
        "curated_duplicate_inputs": 0,
        "curated_domains": dict(sorted(domains.items())),
        "curated_tasks": dict(sorted(tasks.items())),
        "train_path": str(train_path),
        "dev_path": str(dev_path),
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("ALIGNMENT SMOKE DATASET PASS")
    print(f"public train: {len(public_train)}")
    print(f"curated train: {len(curated)}")
    print(f"final train: {len(train_rows)}")
    print(f"dev: {len(dev_rows)}")
    print("evaluation prompt leakage: 0")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
