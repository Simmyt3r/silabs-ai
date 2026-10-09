from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.promotion_gate import assess


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def assess_release(
    capability: dict,
    safety: dict,
    *,
    min_capability_score: float = 0.0,
    min_safety_score: float = 0.0,
    min_capability_delta: float = 0.0,
    min_safety_delta: float = 0.0,
    max_capability_regressions: int = 0,
    max_safety_regressions: int = 0,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    capability_ok, capability_reasons = assess(
        capability,
        min_score_delta=min_capability_delta,
        max_regressions=max_capability_regressions,
        min_candidate_score=min_capability_score,
    )
    if not capability_ok:
        reasons.extend(f"capability: {reason}" for reason in capability_reasons)

    safety_ok, safety_reasons = assess(
        safety,
        min_score_delta=min_safety_delta,
        max_regressions=max_safety_regressions,
        min_candidate_score=min_safety_score,
    )
    if not safety_ok:
        reasons.extend(f"safety: {reason}" for reason in safety_reasons)

    return not reasons, reasons


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply combined Silabs AI capability and safety release gates"
    )
    parser.add_argument("capability_comparison", type=Path)
    parser.add_argument("safety_comparison", type=Path)
    parser.add_argument("--min-capability-score", type=float, default=0.0)
    parser.add_argument("--min-safety-score", type=float, default=0.0)
    parser.add_argument("--min-capability-delta", type=float, default=0.0)
    parser.add_argument("--min-safety-delta", type=float, default=0.0)
    parser.add_argument("--max-capability-regressions", type=int, default=0)
    parser.add_argument("--max-safety-regressions", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    capability = load(args.capability_comparison)
    safety = load(args.safety_comparison)

    passed, reasons = assess_release(
        capability,
        safety,
        min_capability_score=args.min_capability_score,
        min_safety_score=args.min_safety_score,
        min_capability_delta=args.min_capability_delta,
        min_safety_delta=args.min_safety_delta,
        max_capability_regressions=args.max_capability_regressions,
        max_safety_regressions=args.max_safety_regressions,
    )

    result = {
        "passed": passed,
        "capability": {
            "baseline_score": capability.get("baseline_score"),
            "candidate_score": capability.get("candidate_score"),
            "score_delta": capability.get("score_delta"),
            "regressions": len(capability.get("regressions", [])),
        },
        "safety": {
            "baseline_score": safety.get("baseline_score"),
            "candidate_score": safety.get("candidate_score"),
            "score_delta": safety.get("score_delta"),
            "regressions": len(safety.get("regressions", [])),
        },
        "reasons": reasons,
    }

    print(
        "capability: "
        f"{float(capability.get('baseline_score', 0.0)):.1%} -> "
        f"{float(capability.get('candidate_score', 0.0)):.1%}"
    )
    print(
        "safety: "
        f"{float(safety.get('baseline_score', 0.0)):.1%} -> "
        f"{float(safety.get('candidate_score', 0.0)):.1%}"
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"release gate report: {args.output}")

    if not passed:
        for reason in reasons:
            print(f"RELEASE GATE FAIL: {reason}")
        raise SystemExit(1)

    print("SILABS AI RELEASE GATE: PASS")


if __name__ == "__main__":
    main()
