import json

from silabs_ai.retrieval import JsonlKnowledgeRetriever


def _write_jsonl(path, records):
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def test_verified_retrieval_ranks_relevant_record_first(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write_jsonl(
        path,
        [
            {
                "title": "UniXpress",
                "text": "UniXpress helps students access past questions and verified solutions.",
                "source": "silabs://unixpress/overview",
                "verified": True,
            },
            {
                "title": "Silabs",
                "text": "Simeon's Laboratories and Co Technologies Ltd builds technology products.",
                "source": "silabs://company/overview",
                "verified": True,
            },
        ],
    )

    retriever = JsonlKnowledgeRetriever(path)
    results = retriever.retrieve("Where can students get past questions?", limit=2)

    assert results
    assert results[0].source == "silabs://unixpress/overview"
    assert results[0].score is not None
    assert results[0].score > 0


def test_unverified_records_are_excluded_by_default(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write_jsonl(
        path,
        [
            {
                "text": "Secret prototype fact.",
                "source": "silabs://draft",
                "verified": False,
            },
            {
                "text": "Verified public product fact.",
                "source": "silabs://verified",
                "verified": True,
            },
        ],
    )

    retriever = JsonlKnowledgeRetriever(path)
    results = retriever.retrieve("prototype fact verified product", limit=10)

    assert all(item.source != "silabs://draft" for item in results)
    assert any(item.source == "silabs://verified" for item in results)


def test_missing_knowledge_file_returns_no_results(tmp_path):
    retriever = JsonlKnowledgeRetriever(tmp_path / "missing.jsonl")

    assert retriever.retrieve("anything") == []


def test_invalid_json_reports_line_number(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    path.write_text('{"text":"valid","source":"one"}\nnot-json\n', encoding="utf-8")

    try:
        JsonlKnowledgeRetriever(path)
    except ValueError as exc:
        assert ":2" in str(exc)
    else:
        raise AssertionError("Expected invalid JSONL to raise ValueError")


def test_zero_limit_returns_no_results(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write_jsonl(
        path,
        [{"text": "Silabs AI knowledge.", "source": "silabs://ai"}],
    )

    retriever = JsonlKnowledgeRetriever(path)

    assert retriever.retrieve("Silabs", limit=0) == []
