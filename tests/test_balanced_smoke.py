import json

from scripts.make_balanced_smoke import distribution, select_balanced


def write_rows(path, datasets):
    rows = []
    for name, count in datasets.items():
        for index in range(count):
            rows.append({
                "id": f"{name}-{index}",
                "dataset": name,
                "instruction": "Answer.",
                "input": f"Question {index}",
                "output": f"Answer {index}",
            })
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_balanced_sampler_represents_each_dataset(tmp_path):
    path = tmp_path / "train.jsonl"
    write_rows(path, {"a": 10, "b": 10, "c": 10})

    selected = select_balanced(path, 9)

    assert distribution(selected) == {"a": 3, "b": 3, "c": 3}


def test_balanced_sampler_is_deterministic(tmp_path):
    path = tmp_path / "train.jsonl"
    write_rows(path, {"a": 7, "b": 5})

    first = select_balanced(path, 8)
    second = select_balanced(path, 8)

    assert [row["id"] for row in first] == [row["id"] for row in second]


def test_balanced_sampler_fills_from_larger_groups(tmp_path):
    path = tmp_path / "train.jsonl"
    write_rows(path, {"small": 1, "large": 10})

    selected = select_balanced(path, 6)

    assert len(selected) == 6
    assert distribution(selected)["small"] == 1
    assert distribution(selected)["large"] == 5
