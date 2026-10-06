from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from silabs_ai.config import Settings
from silabs_ai.engine import SilabsAIEngine


def repeated_ngram(text: str, n: int = 4, threshold: int = 4) -> bool:
    tokens = re.findall(r"\w+", text.lower())
    if len(tokens) < n:
        return False
    counts: dict[tuple[str, ...], int] = {}
    for index in range(len(tokens) - n + 1):
        gram = tuple(tokens[index : index + n])
        counts[gram] = counts.get(gram, 0) + 1
    return max(counts.values(), default=0) >= threshold


def load_cases(path: Path) -> list[dict]:
    cases = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def judge(case: dict, output: str) -> tuple[bool, list[str]]:
    failures = []
    normalized = output.strip().lower()

    if "exact" in case and normalized != str(case["exact"]).strip().lower():
        failures.append("exact_mismatch")

    for expected in case.get("must_contain", []):
        if expected.lower() not in normalized:
            failures.append(f"missing:{expected}")

    for banned in case.get("must_not_contain", []):
        if banned.lower() in normalized:
            failures.append(f"contains_banned:{banned}")

    if repeated_ngram(output):
        failures.append("ngram_repetition")

    return not failures, failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Silabs AI behavioral evaluation")
    parser.add_argument("--model", default=None, help="Model ID or local checkpoint")
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.jsonl"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()

    settings = Settings(model_id=args.model) if args.model else Settings()
    engine = SilabsAIEngine(settings)
    cases = load_cases(args.cases)

    results = []
    passes = 0
    for case in cases:
        generated = engine.chat(case["prompt"], temperature=0.0)
        passed, failures = judge(case, generated.text)
        passes += int(passed)
        results.append({
            "id": case["id"],
            "category": case.get("category"),
            "prompt": case["prompt"],
            "output": generated.text,
            "passed": passed,
            "failures": failures,
        })
        print(f"[{'PASS' if passed else 'FAIL'}] {case['id']}: {generated.text}")

    score = passes / len(cases) if cases else 0.0
    report = {
        "model": settings.model_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": passes,
        "total": len(cases),
        "score": score,
        "results": results,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    filename = args.report_dir / "behavior_eval.json"
    filename.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"score: {passes}/{len(cases)} ({score:.1%})")
    print(f"report: {filename}")


if __name__ == "__main__":
    main()
