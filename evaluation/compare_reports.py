from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_report(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "results" not in data:
        raise ValueError(f"{path} is not a Silabs evaluation report")
    return data


def index_results(report: dict) -> dict[str, dict]:
    return {row["id"]: row for row in report.get("results", [])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two Silabs AI eval reports")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    baseline = load_report(args.baseline)
    candidate = load_report(args.candidate)
    base_rows = index_results(baseline)
    cand_rows = index_results(candidate)

    shared = sorted(set(base_rows) & set(cand_rows))
    regressions = []
    improvements = []
    unchanged = []

    for case_id in shared:
        before = bool(base_rows[case_id].get("passed"))
        after = bool(cand_rows[case_id].get("passed"))
        row = {
            "id": case_id,
            "baseline_passed": before,
            "candidate_passed": after,
            "baseline_output": base_rows[case_id].get("output"),
            "candidate_output": cand_rows[case_id].get("output"),
        }
        if before and not after:
            regressions.append(row)
        elif not before and after:
            improvements.append(row)
        else:
            unchanged.append(row)

    base_score = float(baseline.get("score", 0.0))
    candidate_score = float(candidate.get("score", 0.0))
    comparison = {
        "baseline_model": baseline.get("model"),
        "candidate_model": candidate.get("model"),
        "baseline_score": base_score,
        "candidate_score": candidate_score,
        "score_delta": candidate_score - base_score,
        "shared_cases": len(shared),
        "improvements": improvements,
        "regressions": regressions,
        "unchanged": unchanged,
    }

    print(f"baseline: {base_score:.1%}")
    print(f"candidate: {candidate_score:.1%}")
    print(f"delta: {candidate_score - base_score:+.1%}")
    print(f"improvements: {len(improvements)}")
    print(f"regressions: {len(regressions)}")

    if regressions:
        print("regressed cases:")
        for row in regressions:
            print(f"  - {row['id']}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"comparison: {args.output}")


if __name__ == "__main__":
    main()
