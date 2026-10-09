import json
from pathlib import Path

import pytest

from scripts.build_alignment_smoke import (
    normalize,
    read_curated,
    read_eval_prompts,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_normalize_collapses_case_and_whitespace():
    assert normalize("  Hello   WORLD  ") == "hello world"


def test_curated_records_are_canonicalized(tmp_path):
    path = tmp_path / "curated.json"
    path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "task": "reasoning",
                        "domain": "reasoning",
                        "instruction": "Think carefully.",
                        "input": "A is above B. Who is above?",
                        "output": "A is above.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    rows = read_curated(path)

    assert len(rows) == 1
    assert rows[0]["dataset"] == "silabs_alignment_v1"
    assert rows[0]["metadata"]["benchmark_disjoint_required"] is True
    assert rows[0]["id"].startswith("silabs_alignment_v1_")


def test_eval_prompt_lookup_detects_exact_normalized_match(tmp_path):
    cases = tmp_path / "cases.jsonl"
    write_jsonl(
        cases,
        [
            {
                "id": "case_1",
                "category": "reasoning",
                "prompt": "Who is tallest?",
                "must_match": ["Ada"],
            }
        ],
    )

    prompts = read_eval_prompts([cases])

    assert normalize(" who   is TALLEST? ") in prompts


def test_repo_alignment_set_is_disjoint_from_evaluations():
    curated = read_curated(Path("datasets/curated/alignment_v1.json"))
    eval_prompts = read_eval_prompts(
        [
            Path("evaluation/cases_extended_v2.jsonl"),
            Path("evaluation/cases_safety.jsonl"),
        ]
    )

    overlaps = [
        row["input"]
        for row in curated
        if normalize(row["input"]) in eval_prompts
    ]

    assert overlaps == []
