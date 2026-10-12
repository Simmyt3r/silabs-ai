from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from silabs_ai.retrieval import KnowledgeRecord


def validate_knowledge(path: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    records: list[KnowledgeRecord] = []
    normalized_texts: list[str] = []

    if not path.exists():
        return {
            "passed": False,
            "records": 0,
            "verified": 0,
            "unverified": 0,
            "errors": [f"knowledge file not found: {path}"],
            "warnings": [],
        }

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                continue

            if not isinstance(data, dict):
                errors.append(f"line {line_number}: record must be a JSON object")
                continue

            try:
                record = KnowledgeRecord.from_mapping(data)
            except ValueError as exc:
                errors.append(f"line {line_number}: {exc}")
                continue

            records.append(record)
            normalized_texts.append(" ".join(record.text.lower().split()))

            if record.source.lower() in {"unknown", "none", "n/a"}:
                warnings.append(
                    f"line {line_number}: weak provenance source={record.source!r}"
                )

    counts = Counter(normalized_texts)
    duplicate_texts = sum(counts.values()) - len(counts)
    if duplicate_texts:
        warnings.append(f"duplicate text records: {duplicate_texts}")

    verified = sum(record.verified for record in records)
    unverified = len(records) - verified

    if not records and not errors:
        warnings.append("knowledge file contains no records")

    return {
        "passed": not errors,
        "records": len(records),
        "verified": verified,
        "unverified": unverified,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a Silabs AI JSONL knowledge file before RAG use."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("knowledge/verified.jsonl"),
    )
    args = parser.parse_args()

    report = validate_knowledge(args.path)

    print(f"knowledge: {args.path}")
    print(f"records: {report['records']}")
    print(f"verified: {report['verified']}")
    print(f"unverified: {report['unverified']}")

    for warning in report["warnings"]:
        print(f"WARNING: {warning}")

    for error in report["errors"]:
        print(f"ERROR: {error}")

    if not report["passed"]:
        raise SystemExit(1)

    print("SILABS KNOWLEDGE VALIDATION: PASS")


if __name__ == "__main__":
    main()
