from scripts.download_training_datasets import (
    COMMERCIAL_EXCLUDE,
    DATASETS,
    format_choices,
    record,
    stable_id,
)


def test_dataset_ids_are_deterministic():
    assert stable_id("gsm8k", "What is 2+3?", "5") == stable_id(
        "gsm8k", "What is 2+3?", "5"
    )


def test_record_uses_canonical_schema():
    row = record(
        "gsm8k",
        "math_reasoning",
        "Solve accurately.",
        "What is 2+3?",
        "5",
        {"domain": "mathematics"},
    )

    assert set(row) == {
        "id",
        "dataset",
        "task",
        "domain",
        "instruction",
        "input",
        "output",
        "metadata",
    }
    assert row["dataset"] == "gsm8k"
    assert row["domain"] == "mathematics"
    assert row["metadata"]["source_repo"] == "openai/gsm8k"


def test_choice_format_is_stable():
    text = format_choices("Question?", ["A", "B"], ["One", "Two"])
    assert text == "Question?\n\nChoices:\nA. One\nB. Two"


def test_commercial_profile_excludes_unresolved_sources():
    assert COMMERCIAL_EXCLUDE == {"sciq", "openbookqa"}
    assert DATASETS["sciq"]["commercial_status"] == "research_only"
    assert DATASETS["openbookqa"]["commercial_status"] == "review_required"
