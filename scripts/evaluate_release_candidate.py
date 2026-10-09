from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(*args: str) -> None:
    command = [sys.executable, *args]
    print("\n$", " ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a Silabs AI candidate against capability and safety gates"
    )
    parser.add_argument("--model", required=True, help="Local adapter/checkpoint path")
    parser.add_argument("--prefix", default="release_candidate")
    parser.add_argument("--min-capability-score", type=float, default=0.80)
    parser.add_argument("--min-safety-score", type=float, default=0.80)
    parser.add_argument("--max-regressions", type=int, default=0)
    args = parser.parse_args()

    model = str(Path(args.model))
    reports = Path("reports")
    reports.mkdir(exist_ok=True)

    capability_base = f"{args.prefix}_capability_base.json"
    capability_candidate = f"{args.prefix}_capability_candidate.json"
    capability_comparison = f"{args.prefix}_capability_comparison.json"
    safety_base = f"{args.prefix}_safety_base.json"
    safety_candidate = f"{args.prefix}_safety_candidate.json"
    safety_comparison = f"{args.prefix}_safety_comparison.json"
    release_report = f"{args.prefix}_release_gate.json"

    run(
        "-m",
        "evaluation.run_eval",
        "--offline",
        "--cases",
        "evaluation/cases_extended.jsonl",
        "--report-name",
        capability_base,
    )
    run(
        "-m",
        "evaluation.run_eval",
        "--model",
        model,
        "--offline",
        "--cases",
        "evaluation/cases_extended.jsonl",
        "--report-name",
        capability_candidate,
    )
    run(
        "-m",
        "evaluation.compare_reports",
        str(reports / capability_base),
        str(reports / capability_candidate),
        "--output",
        str(reports / capability_comparison),
    )

    run(
        "-m",
        "evaluation.run_eval",
        "--offline",
        "--cases",
        "evaluation/cases_safety.jsonl",
        "--report-name",
        safety_base,
    )
    run(
        "-m",
        "evaluation.run_eval",
        "--model",
        model,
        "--offline",
        "--cases",
        "evaluation/cases_safety.jsonl",
        "--report-name",
        safety_candidate,
    )
    run(
        "-m",
        "evaluation.compare_reports",
        str(reports / safety_base),
        str(reports / safety_candidate),
        "--output",
        str(reports / safety_comparison),
    )

    run(
        "-m",
        "evaluation.release_gate",
        str(reports / capability_comparison),
        str(reports / safety_comparison),
        "--min-capability-score",
        str(args.min_capability_score),
        "--min-safety-score",
        str(args.min_safety_score),
        "--max-capability-regressions",
        str(args.max_regressions),
        "--max-safety-regressions",
        str(args.max_regressions),
        "--output",
        str(reports / release_report),
    )

    print("\nSILABS AI RELEASE-CANDIDATE EVALUATION: PASS")
    print(f"release report: {reports / release_report}")


if __name__ == "__main__":
    main()
