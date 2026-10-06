from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from pathlib import Path

from .data import DatasetFormatError, iter_jsonl, normalize_record


def fingerprint(messages: list[dict[str, str]]) -> str:
    canonical = "\n".join(f"{m['role']}:{m['content'].strip()}" for m in messages)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate(path: Path) -> dict[str, int]:
    seen: set[str] = set()
    duplicates = 0
    roles: Counter[str] = Counter()
    records = 0

    for line_number, record in iter_jsonl(path):
        try:
            messages = normalize_record(record)
        except DatasetFormatError as exc:
            raise DatasetFormatError(f"{path}:{line_number}: {exc}") from exc

        records += 1
        for message in messages:
            roles[message["role"]] += 1

        fp = fingerprint(messages)
        if fp in seen:
            duplicates += 1
        seen.add(fp)

    if records == 0:
        raise DatasetFormatError(f"{path}: no usable records")

    return {
        "records": records,
        "duplicates": duplicates,
        "system_messages": roles["system"],
        "user_messages": roles["user"],
        "assistant_messages": roles["assistant"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Silabs AI JSONL data")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    stats = validate(args.path)
    print("VALIDATION PASS")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
