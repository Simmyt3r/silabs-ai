from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
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
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {path}:{line_number}") from exc
            if "id" not in case or "prompt" not in case:
                raise ValueError(f"Case on {path}:{line_number} requires id and prompt")
            cases.append(case)
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

    for pattern in case.get("must_match", []):
        if re.search(pattern, output, flags=re.IGNORECASE | re.MULTILINE) is None:
            failures.append(f"regex_mismatch:{pattern}")

    for pattern in case.get("must_not_match", []):
        if re.search(pattern, output, flags=re.IGNORECASE | re.MULTILINE) is not None:
            failures.append(f"forbidden_regex:{pattern}")

    word_count = len(re.findall(r"\b\w+\b", output))
    if case.get("max_words") is not None and word_count > int(case["max_words"]):
        failures.append(f"too_long:{word_count}")

    if case.get("min_words") is not None and word_count < int(case["min_words"]):
        failures.append(f"too_short:{word_count}")

    if repeated_ngram(output):
        failures.append("ngram_repetition")

    return not failures, failures


def resolve_settings(model_arg: str | None, offline: bool) -> Settings:
    if not model_arg:
        return Settings(allow_remote_model_download=not offline)

    candidate = Path(model_arg).expanduser()
    if candidate.exists():
        if (candidate / "adapter_config.json").is_file():
            return Settings(
                adapter_path=str(candidate),
                allow_remote_model_download=not offline,
            )
        return Settings(
            model_id=model_arg,
            model_path=str(candidate),
            allow_remote_model_download=False,
        )

    return Settings(
        model_id=model_arg,
        model_path=None,
        allow_remote_model_download=not offline,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Silabs AI behavioral evaluation")
    parser.add_argument("--model", default=None, help="Model ID or local checkpoint")
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.jsonl"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports"))
    parser.add_argument("--report-name", default="behavior_eval.json")
    parser.add_argument("--offline", action="store_true", help="Require local model files")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    args = parser.parse_args()

    settings = resolve_settings(args.model, args.offline)
    engine = SilabsAIEngine(settings)
    cases = load_cases(args.cases)

    results = []
    passes = 0
    category_totals: dict[str, int] = defaultdict(int)
    category_passes: dict[str, int] = defaultdict(int)
    started = time.perf_counter()

    for case in cases:
        category = case.get("category", "uncategorized")
        category_totals[category] += 1

        case_started = time.perf_counter()
        generated = engine.chat(
            case["prompt"],
            temperature=0.0,
            max_new_tokens=args.max_new_tokens,
        )
        elapsed = time.perf_counter() - case_started

        passed, failures = judge(case, generated.text)
        passes += int(passed)
        category_passes[category] += int(passed)

        results.append({
            "id": case["id"],
            "category": category,
            "prompt": case["prompt"],
            "output": generated.text,
            "passed": passed,
            "failures": failures,
            "input_tokens": generated.input_tokens,
            "output_tokens": generated.output_tokens,
            "latency_seconds": round(elapsed, 4),
        })
        print(
            f"[{'PASS' if passed else 'FAIL'}] {case['id']} "
            f"({elapsed:.2f}s): {generated.text}"
        )

    total_elapsed = time.perf_counter() - started
    score = passes / len(cases) if cases else 0.0
    category_scores = {
        category: {
            "passed": category_passes[category],
            "total": total,
            "score": category_passes[category] / total if total else 0.0,
        }
        for category, total in sorted(category_totals.items())
    }

    report = {
        "schema_version": 1,
        "model": settings.model_id,
        "model_path": settings.model_path,
        "adapter_path": settings.adapter_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": passes,
        "total": len(cases),
        "score": score,
        "elapsed_seconds": round(total_elapsed, 4),
        "category_scores": category_scores,
        "results": results,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    filename = args.report_dir / args.report_name
    filename.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("")
    print("Category scores:")
    for category, stats in category_scores.items():
        print(
            f"  {category}: {stats['passed']}/{stats['total']} "
            f"({stats['score']:.1%})"
        )
    print(f"overall: {passes}/{len(cases)} ({score:.1%})")
    print(f"elapsed: {total_elapsed:.2f}s")
    print(f"report: {filename}")


if __name__ == "__main__":
    main()
