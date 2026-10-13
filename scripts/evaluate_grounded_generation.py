from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from silabs_ai.config import Settings
from silabs_ai.engine import SilabsAIEngine


_CITATION_RE = re.compile(r"\[(S\d+)\]")


DEFAULT_CASES = [
    "How do spatial indexes work in PostGIS?",
    "How do I initialize and verify a payment with Paystack?",
    "How do responsive design breakpoints work in Tailwind CSS?",
    "How do routes and view functions work in Flask?",
    "How do I create and use a Python virtual environment?",
    "How does deploying a web application to Vercel work?",
]


def evaluate_case(engine: SilabsAIEngine, query: str, max_new_tokens: int) -> dict:
    started = time.perf_counter()
    result = engine.chat(
        query,
        temperature=0.0,
        max_new_tokens=max_new_tokens,
    )
    elapsed = time.perf_counter() - started

    available = {
        item.citation
        for item in result.sources
        if item.citation
    }
    cited = set(_CITATION_RE.findall(result.text))
    invented = sorted(cited - available)
    valid = sorted(cited & available)

    # For a normal knowledge query with retrieved evidence, require at least
    # one valid citation and forbid invented labels. If nothing was retrieved,
    # the model cannot be expected to cite a source.
    citation_required = bool(result.sources)
    passed = (not invented) and (not citation_required or bool(valid))

    return {
        "query": query,
        "passed": passed,
        "elapsed_seconds": round(elapsed, 3),
        "text": result.text,
        "available_citations": sorted(available),
        "cited": sorted(cited),
        "valid_citations": valid,
        "invented_citations": invented,
        "sources": [
            {
                "citation": item.citation,
                "source": item.source,
                "score": item.score,
            }
            for item in result.sources
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate grounded Silabs AI generation and citation integrity."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        help="Optional JSONL file with a 'query' field per line.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    args = parser.parse_args()

    if args.cases:
        queries = []
        for raw in args.cases.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            row = json.loads(raw)
            query = str(row.get("query", "")).strip()
            if query:
                queries.append(query)
    else:
        queries = list(DEFAULT_CASES)

    settings = Settings(_env_file=None)
    engine = SilabsAIEngine(settings)

    rows = []
    for index, query in enumerate(queries, start=1):
        print(f"[{index}/{len(queries)}] {query}", flush=True)
        row = evaluate_case(engine, query, args.max_new_tokens)
        rows.append(row)
        status = "PASS" if row["passed"] else "FAIL"
        print(
            f"  {status} | cited={row['cited']} "
            f"| available={row['available_citations']} "
            f"| {row['elapsed_seconds']}s",
            flush=True,
        )

    passed = sum(1 for row in rows if row["passed"])
    total = len(rows)
    report = {
        "model": settings.model_id,
        "cases": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "results": rows,
    }

    print("\nSILABS GROUNDED GENERATION")
    print(f"cases: {total}")
    print(f"passed: {passed}")
    print(f"pass rate: {report['pass_rate']:.1%}")

    failures = [row for row in rows if not row["passed"]]
    if failures:
        print("\nFAILURES:")
        for row in failures:
            print(f"- {row['query']}")
            print(f"  cited: {row['cited']}")
            print(f"  available: {row['available_citations']}")
            print(f"  invented: {row['invented_citations']}")
            print(f"  answer: {row['text'][:500]}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nreport: {args.output}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
