from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from training.data import iter_jsonl


def stable_rank(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def select_balanced(
    path: Path,
    count: int,
    *,
    group_field: str = "dataset",
) -> list[dict]:
    if count < 1:
        raise ValueError("count must be at least 1")

    groups: dict[str, list[dict]] = defaultdict(list)
    for _, record in iter_jsonl(path):
        value = str(record.get(group_field) or "<missing>").strip() or "<missing>"
        groups[value].append(record)

    if not groups:
        raise ValueError(f"No records found in {path}")

    for rows in groups.values():
        rows.sort(key=stable_rank)

    names = sorted(groups)
    offsets = {name: 0 for name in names}
    selected: list[dict] = []

    # Deterministic round-robin sampling keeps the subset approximately balanced
    # across source datasets while still using stable hash ranking within each
    # source. Exhausted small groups are skipped and larger groups fill the rest.
    while len(selected) < count:
        progressed = False
        for name in names:
            index = offsets[name]
            rows = groups[name]
            if index >= len(rows):
                continue
            selected.append(rows[index])
            offsets[name] = index + 1
            progressed = True
            if len(selected) >= count:
                break
        if not progressed:
            break

    return selected


def distribution(rows: list[dict], field: str = "dataset") -> dict[str, int]:
    counts = Counter(str(row.get(field) or "<missing>") for row in rows)
    return dict(sorted(counts.items()))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create deterministic dataset-balanced Silabs AI smoke subsets"
    )
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--train-count", type=int, default=400)
    parser.add_argument("--dev-count", type=int, default=100)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets/processed/smoke_balanced"),
    )
    args = parser.parse_args()

    train_rows = select_balanced(args.train, args.train_count)
    dev_rows = select_balanced(args.dev, args.dev_count)

    train_path = args.output_dir / "train.jsonl"
    dev_path = args.output_dir / "dev.jsonl"
    write_jsonl(train_path, train_rows)
    write_jsonl(dev_path, dev_rows)

    report = {
        "schema_version": 1,
        "strategy": "deterministic round-robin by dataset; sha256 order within dataset",
        "train": {
            "records": len(train_rows),
            "distribution": distribution(train_rows),
            "path": str(train_path),
        },
        "dev": {
            "records": len(dev_rows),
            "distribution": distribution(dev_rows),
            "path": str(dev_path),
        },
    }

    report_path = args.output_dir / "manifest.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("BALANCED SMOKE DATASET PASS")
    print(f"train: {len(train_rows)} -> {train_path}")
    print(json.dumps(report["train"]["distribution"], indent=2))
    print(f"dev: {len(dev_rows)} -> {dev_path}")
    print(json.dumps(report["dev"]["distribution"], indent=2))
    print(f"manifest: {report_path}")


if __name__ == "__main__":
    main()
