from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


RECOMMENDED_FIELDS = (
    "source_kind",
    "trust_tier",
    "authority",
    "retrieved_at",
)


def audit_knowledge(path: Path, manifest_path: Path | None = None) -> dict:
    report = {
        "passed": True,
        "records": 0,
        "verified": 0,
        "unverified": 0,
        "source_kinds": Counter(),
        "domains": Counter(),
        "trust_tiers": Counter(),
        "missing_metadata": Counter(),
        "duplicate_hashes": 0,
        "missing_content_hashes": 0,
        "manifest": None,
        "errors": [],
        "warnings": [],
    }

    if not path.exists():
        report["passed"] = False
        report["errors"].append(f"knowledge file not found: {path}")
        return report

    seen_hashes: set[str] = set()

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue

            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                report["passed"] = False
                report["errors"].append(
                    f"line {line_number}: invalid JSON: {exc.msg}"
                )
                continue

            if not isinstance(row, dict):
                report["passed"] = False
                report["errors"].append(
                    f"line {line_number}: record must be a JSON object"
                )
                continue

            report["records"] += 1
            if bool(row.get("verified", True)):
                report["verified"] += 1
            else:
                report["unverified"] += 1

            source_kind = str(row.get("source_kind") or "unknown").strip()
            report["source_kinds"][source_kind] += 1

            domain = str(row.get("domain") or "unknown").strip()
            report["domains"][domain] += 1

            trust_tier = str(row.get("trust_tier") or "unknown").strip()
            report["trust_tiers"][trust_tier] += 1

            for field in RECOMMENDED_FIELDS:
                if not str(row.get(field) or "").strip():
                    report["missing_metadata"][field] += 1

            content_hash = str(row.get("content_hash") or "").strip()
            if not content_hash:
                report["missing_content_hashes"] += 1
            elif content_hash in seen_hashes:
                report["duplicate_hashes"] += 1
            else:
                seen_hashes.add(content_hash)

    if report["records"] == 0:
        report["warnings"].append("knowledge corpus contains no records")

    if report["unverified"]:
        report["warnings"].append(
            f"unverified records present: {report['unverified']}"
        )

    if report["duplicate_hashes"]:
        report["warnings"].append(
            f"duplicate content hashes: {report['duplicate_hashes']}"
        )

    if report["missing_content_hashes"]:
        report["warnings"].append(
            f"records missing content_hash: {report['missing_content_hashes']}"
        )

    for field, count in sorted(report["missing_metadata"].items()):
        if count:
            report["warnings"].append(
                f"records missing {field}: {count}"
            )

    if manifest_path is not None:
        if not manifest_path.exists():
            report["warnings"].append(
                f"manifest file not found: {manifest_path}"
            )
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                report["passed"] = False
                report["errors"].append(
                    f"invalid manifest JSON: {exc.msg}"
                )
            else:
                report["manifest"] = manifest
                expected = (
                    manifest.get("stats", {}).get("chunks_written")
                    if isinstance(manifest, dict)
                    else None
                )
                if isinstance(expected, int) and expected != report["records"]:
                    report["warnings"].append(
                        "manifest chunks_written does not match corpus records: "
                        f"{expected} != {report['records']}"
                    )

    for key in ("source_kinds", "domains", "trust_tiers", "missing_metadata"):
        report[key] = dict(report[key])

    return report


def _print_counter(title: str, values: dict[str, int]) -> None:
    print(title + ":")
    if not values:
        print("  none")
        return
    for key, value in sorted(values.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit an expanded Silabs AI knowledge corpus before RAG use."
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = audit_knowledge(args.path, args.manifest)

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"knowledge: {args.path}")
        print(f"records: {report['records']}")
        print(f"verified: {report['verified']}")
        print(f"unverified: {report['unverified']}")
        print(f"duplicate hashes: {report['duplicate_hashes']}")
        print(f"missing content hashes: {report['missing_content_hashes']}")
        _print_counter("source kinds", report["source_kinds"])
        _print_counter("trust tiers", report["trust_tiers"])
        _print_counter("domains", report["domains"])

        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")

    if not report["passed"]:
        raise SystemExit(1)

    if not args.as_json:
        print("SILABS KNOWLEDGE AUDIT: PASS")


if __name__ == "__main__":
    main()
