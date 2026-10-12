import json

from scripts.validate_knowledge import validate_knowledge


def _write(path, rows):
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_validate_knowledge_passes_valid_records(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write(
        path,
        [
            {
                "title": "Silabs AI",
                "text": "Silabs AI is an AI system built by Simeon's Laboratories and Co Technologies Ltd.",
                "source": "silabs://company/ai",
                "verified": True,
            },
            {
                "title": "UniXpress",
                "text": "UniXpress is a student-focused platform.",
                "source": "silabs://unixpress/overview",
                "verified": False,
            },
        ],
    )

    report = validate_knowledge(path)

    assert report["passed"] is True
    assert report["records"] == 2
    assert report["verified"] == 1
    assert report["unverified"] == 1
    assert report["errors"] == []


def test_validate_knowledge_rejects_missing_source(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write(
        path,
        [{"text": "A fact without provenance.", "verified": True}],
    )

    report = validate_knowledge(path)

    assert report["passed"] is False
    assert report["errors"]


def test_validate_knowledge_rejects_invalid_json(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    path.write_text("not-json\n", encoding="utf-8")

    report = validate_knowledge(path)

    assert report["passed"] is False
    assert "invalid JSON" in report["errors"][0]


def test_validate_knowledge_warns_on_duplicate_text(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write(
        path,
        [
            {"text": "Same fact.", "source": "one", "verified": True},
            {"text": "Same fact.", "source": "two", "verified": True},
        ],
    )

    report = validate_knowledge(path)

    assert report["passed"] is True
    assert any("duplicate text" in warning for warning in report["warnings"])
