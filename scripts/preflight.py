from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

try:
    import torch
except ImportError:
    torch = None

try:
    from transformers import __version__ as transformers_version
except ImportError:
    transformers_version = "not-installed"

from silabs_ai.config import get_settings
from training.data import iter_jsonl, normalize_record
from training.validate_dataset import fingerprint, validate


def dataset_fingerprints(path: Path) -> set[str]:
    values = set()
    for _, record in iter_jsonl(path):
        values.add(fingerprint(normalize_record(record)))
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description="Silabs AI environment/data preflight")
    parser.add_argument("--train", type=Path)
    parser.add_argument("--dev", type=Path)
    args = parser.parse_args()

    settings = get_settings()
    print("SILABS AI PREFLIGHT")
    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")
    print(f"torch: {torch.__version__ if torch is not None else 'not-installed'}")
    print(f"transformers: {transformers_version}")
    cuda_available = bool(torch is not None and torch.cuda.is_available())
    print(f"cuda_available: {cuda_available}")
    if cuda_available:
        print(f"gpu: {torch.cuda.get_device_name(0)}")
    print(f"model: {settings.model_id}")

    if args.train:
        print(f"train: {validate(args.train)}")
    if args.dev:
        print(f"dev: {validate(args.dev)}")
    if args.train and args.dev:
        overlap = dataset_fingerprints(args.train) & dataset_fingerprints(args.dev)
        print(f"exact_train_dev_overlap: {len(overlap)}")
        if overlap:
            raise SystemExit("PREFLIGHT FAIL: train/dev overlap detected")

    print("PREFLIGHT PASS")


if __name__ == "__main__":
    main()
