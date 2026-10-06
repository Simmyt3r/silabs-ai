from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from training.data import iter_jsonl, normalize_record
from training.validate_dataset import fingerprint, validate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def distribution(path: Path, field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for _, record in iter_jsonl(path):
        value = record.get(field)
        key = str(value).strip() if value is not None else ""
        counts[key or "<missing>"] += 1
    return dict(sorted(counts.items()))


def normalized_fingerprints(path: Path) -> set[str]:
    return {
        fingerprint(normalize_record(record))
        for _, record in iter_jsonl(path)
    }


def select_smoke_records(path: Path, count: int) -> list[dict]:
    ranked: list[tuple[str, dict]] = []
    for _, record in iter_jsonl(path):
        stable = json.dumps(record, sort_keys=True, ensure_ascii=False)
        rank = hashlib.sha256(stable.encode("utf-8")).hexdigest()
        ranked.append((rank, record))
    ranked.sort(key=lambda item: item[0])
    return [record for _, record in ranked[:count]]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Freeze metadata for a Silabs AI dataset release"
    )
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--name", default="silabs-v1")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("datasets/registry/releases/silabs-v1.json"),
    )
    parser.add_argument("--smoke-train", type=int, default=400)
    parser.add_argument("--smoke-dev", type=int, default=100)
    parser.add_argument(
        "--smoke-dir",
        type=Path,
        default=Path("datasets/processed/smoke"),
    )
    args = parser.parse_args()

    train_stats = validate(args.train)
    dev_stats = validate(args.dev)

    train_fp = normalized_fingerprints(args.train)
    dev_fp = normalized_fingerprints(args.dev)
    overlap = train_fp & dev_fp
    if overlap:
        raise SystemExit(
            f"RELEASE FAIL: {len(overlap)} exact normalized train/dev overlaps"
        )

    train_smoke = select_smoke_records(args.train, args.smoke_train)
    dev_smoke = select_smoke_records(args.dev, args.smoke_dev)
    smoke_train_path = args.smoke_dir / "train.jsonl"
    smoke_dev_path = args.smoke_dir / "dev.jsonl"
    write_jsonl(smoke_train_path, train_smoke)
    write_jsonl(smoke_dev_path, dev_smoke)

    manifest = {
        "schema_version": 1,
        "release": args.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train": {
            "path": str(args.train),
            "sha256": sha256_file(args.train),
            "stats": train_stats,
            "unique_normalized_records": len(train_fp),
            "dataset_distribution": distribution(args.train, "dataset"),
            "task_distribution": distribution(args.train, "task"),
            "domain_distribution": distribution(args.train, "domain"),
        },
        "dev": {
            "path": str(args.dev),
            "sha256": sha256_file(args.dev),
            "stats": dev_stats,
            "unique_normalized_records": len(dev_fp),
            "dataset_distribution": distribution(args.dev, "dataset"),
            "task_distribution": distribution(args.dev, "task"),
            "domain_distribution": distribution(args.dev, "domain"),
        },
        "exact_normalized_train_dev_overlap": 0,
        "smoke": {
            "selection": "sha256 lexical order of canonical JSON records",
            "train_records": len(train_smoke),
            "dev_records": len(dev_smoke),
            "train_path": str(smoke_train_path),
            "dev_path": str(smoke_dev_path),
        },
    }

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("DATASET RELEASE PASS")
    print(f"release: {args.name}")
    print(f"train_records: {train_stats['records']}")
    print(f"dev_records: {dev_stats['records']}")
    print("exact_train_dev_overlap: 0")
    print(f"manifest: {args.manifest}")
    print(f"smoke_train: {smoke_train_path} ({len(train_smoke)})")
    print(f"smoke_dev: {smoke_dev_path} ({len(dev_smoke)})")


if __name__ == "__main__":
    main()
