import json

from scripts.evaluate_retrieval import evaluate


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_retrieval_benchmark_reports_hit_rates(tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    cases = tmp_path / "cases.jsonl"

    _write_jsonl(
        corpus,
        [
            {
                "title": "PostGIS",
                "text": "PostGIS adds spatial geometry types and spatial indexes to PostgreSQL.",
                "source": "https://github.com/postgis/postgis/blob/master/doc/reference.xml#chunk-1",
                "verified": True,
            },
            {
                "title": "Flask",
                "text": "Flask routes map URL rules to Python view functions.",
                "source": "https://github.com/pallets/flask/blob/main/docs/quickstart.rst#chunk-1",
                "verified": True,
            },
        ],
    )
    _write_jsonl(
        cases,
        [
            {
                "id": "postgis",
                "query": "How do spatial indexes work in PostGIS?",
                "expected_source_contains": ["github.com/postgis/postgis/"],
            },
            {
                "id": "flask",
                "query": "How do Flask routes map to view functions?",
                "expected_source_contains": ["github.com/pallets/flask/"],
            },
        ],
    )

    report = evaluate(corpus, cases)

    assert report["cases"] == 2
    assert report["hit_at_1"] == 1.0
    assert report["hit_at_3"] == 1.0
    assert report["hit_at_5"] == 1.0
    assert report["mrr_at_5"] == 1.0
