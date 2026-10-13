from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from silabs_ai.retrieval import JsonlKnowledgeRetriever


def _load_cases(path: Path) -> list[dict]:
    cases: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: case must be a JSON object")
            if not str(row.get("query", "")).strip():
                raise ValueError(f"{path}:{line_number}: missing query")
            expected = row.get("expected_source_contains")
            if not isinstance(expected, list) or not expected:
                raise ValueError(
                    f"{path}:{line_number}: expected_source_contains must be a non-empty list"
                )
            cases.append(row)
    return cases


def _rank_of_expected(results, expected: list[str]) -> int | None:
    needles = [item.lower() for item in expected]
    for rank, result in enumerate(results, start=1):
        source = (result.source or "").lower()
        if any(needle.lower() in source for needle in needles):
            return rank
    return None


def evaluate(corpus: Path, cases_path: Path, limit: int = 5) -> dict:
    started = time.perf_counter()
    retriever = JsonlKnowledgeRetriever(corpus)
    load_seconds = time.perf_counter() - started

    cases = _load_cases(cases_path)
    rows: list[dict] = []
    reciprocal_rank = 0.0
    hits = {1: 0, 3: 0, 5: 0}
    query_seconds = 0.0

    for case in cases:
        query_started = time.perf_counter()
        results = retriever.retrieve(case["query"], limit=max(limit, 5))
        query_seconds += time.perf_counter() - query_started

        rank = _rank_of_expected(results, case["expected_source_contains"])
        if rank is not None:
            reciprocal_rank += 1.0 / rank
            for cutoff in hits:
                if rank <= cutoff:
                    hits[cutoff] += 1

        rows.append(
            {
                "id": case.get("id"),
                "query": case["query"],
                "expected_source_contains": case["expected_source_contains"],
                "rank": rank,
                "top_results": [
                    {
                        "source": result.source,
                        "score": result.score,
                    }
                    for result in results[:limit]
                ],
            }
        )

    count = len(cases)
    return {
        "corpus": str(corpus),
        "cases": count,
        "load_seconds": round(load_seconds, 3),
        "query_seconds": round(query_seconds, 3),
        "avg_query_seconds": round(query_seconds / count, 4) if count else 0.0,
        "hit_at_1": round(hits[1] / count, 4) if count else 0.0,
        "hit_at_3": round(hits[3] / count, 4) if count else 0.0,
        "hit_at_5": round(hits[5] / count, 4) if count else 0.0,
        "mrr_at_5": round(reciprocal_rank / count, 4) if count else 0.0,
        "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Silabs AI lexical retrieval hit@k and MRR."
    )
    parser.add_argument("corpus", type=Path)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("evaluation/retrieval_cases_v1.jsonl"),
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = evaluate(args.corpus, args.cases, limit=args.limit)

    print(f"corpus: {report['corpus']}")
    print(f"cases: {report['cases']}")
    print(f"load seconds: {report['load_seconds']}")
    print(f"average query seconds: {report['avg_query_seconds']}")
    print(f"hit@1: {report['hit_at_1']:.1%}")
    print(f"hit@3: {report['hit_at_3']:.1%}")
    print(f"hit@5: {report['hit_at_5']:.1%}")
    print(f"MRR@5: {report['mrr_at_5']:.4f}")

    failures = [row for row in report["results"] if row["rank"] is None]
    if failures:
        print("\nMISSES:")
        for row in failures:
            print(f"- {row['id']}: {row['query']}")
            for item in row["top_results"][:3]:
                print(f"    {item['score']}: {item['source']}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nreport: {args.output}")


if __name__ == "__main__":
    main()
