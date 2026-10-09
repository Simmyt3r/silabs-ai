from __future__ import annotations

import argparse
import json
from pathlib import Path


def assess(
    comparison: dict,
    *,
    min_score_delta: float = 0.0,
    max_regressions: int = 0,
    min_candidate_score: float = 0.0,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    baseline = float(comparison.get("baseline_score", 0.0))
    candidate = float(comparison.get("candidate_score", 0.0))
    delta = float(comparison.get("score_delta", candidate - baseline))
    regressions = comparison.get("regressions", [])

    if candidate < min_candidate_score:
        reasons.append(
            f"candidate score {candidate:.1%} is below required "
            f"{min_candidate_score:.1%}"
        )
    if delta < min_score_delta:
        reasons.append(
            f"score delta {delta:+.1%} is below required {min_score_delta:+.1%}"
        )
    if len(regressions) > max_regressions:
        reasons.append(
            f"{len(regressions)} regressions exceed allowed {max_regressions}"
        )

    return not reasons, reasons


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply Silabs AI model-promotion rules to a comparison report"
    )
    parser.add_argument("comparison", type=Path)
    parser.add_argument("--min-score-delta", type=float, default=0.0)
    parser.add_argument("--max-regressions", type=int, default=0)
    parser.add_argument("--min-candidate-score", type=float, default=0.0)
    args = parser.parse_args()

    data = json.loads(args.comparison.read_text(encoding="utf-8"))
    passed, reasons = assess(
        data,
        min_score_delta=args.min_score_delta,
        max_regressions=args.max_regressions,
        min_candidate_score=args.min_candidate_score,
    )

    print(f"baseline: {float(data.get('baseline_score', 0.0)):.1%}")
    print(f"candidate: {float(data.get('candidate_score', 0.0)):.1%}")
    print(f"delta: {float(data.get('score_delta', 0.0)):+.1%}")
    print(f"regressions: {len(data.get('regressions', []))}")

    if not passed:
        for reason in reasons:
            print(f"GATE FAIL: {reason}")
        raise SystemExit(1)

    print("PROMOTION GATE: PASS")


if __name__ == "__main__":
    main()
