from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.download_training_datasets import (
    arc_records,
    gsm8k_records,
    hotpot_records,
    oasst_records,
    openmath_records,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def deterministic_take(rows: list[dict], count: int) -> list[dict]:
    return sorted(rows, key=lambda row: str(row.get("id", "")))[:count]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a lightweight commercially screened public smoke set for Qwen."
    )
    parser.add_argument("--train-per-dataset", type=int, default=10)
    parser.add_argument("--dev-per-dataset", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets/processed/qwen_public_smoke"),
    )
    args = parser.parse_args()

    if args.train_per_dataset < 1 or args.dev_per_dataset < 1:
        raise SystemExit("train/dev counts must be at least 1")

    builders = {
        "oasst1": oasst_records,
        "gsm8k": gsm8k_records,
        "arc_easy": lambda: arc_records("arc_easy"),
        "arc_challenge": lambda: arc_records("arc_challenge"),
        "hotpotqa": lambda: hotpot_records(
            limit=args.train_per_dataset + args.dev_per_dataset
        ),
        "openmathinstruct2": lambda: openmath_records(
            limit=args.train_per_dataset + args.dev_per_dataset
        ),
    }

    train: list[dict] = []
    dev: list[dict] = []
    manifest: dict[str, dict[str, int]] = {}

    need = args.train_per_dataset + args.dev_per_dataset

    for name, builder in builders.items():
        print(f"[{name}] collecting {need} candidates...")
        rows = builder()
        rows = deterministic_take(rows, need)
        if len(rows) < need:
            raise RuntimeError(
                f"{name} returned only {len(rows)} usable records; need {need}"
            )

        train_rows = rows[: args.train_per_dataset]
        dev_rows = rows[
            args.train_per_dataset : args.train_per_dataset + args.dev_per_dataset
        ]
        train.extend(train_rows)
        dev.extend(dev_rows)
        manifest[name] = {
            "train": len(train_rows),
            "dev": len(dev_rows),
        }

    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "dev.jsonl", dev)

    report = {
        "schema_version": 1,
        "purpose": "lightweight Qwen public smoke set",
        "commercial_profile": True,
        "train_records": len(train),
        "dev_records": len(dev),
        "datasets": manifest,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    print("QWEN PUBLIC SMOKE PASS")
    print(f"train: {len(train)}")
    print(f"dev: {len(dev)}")
    print(f"manifest: {args.output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
