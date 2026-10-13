from silabs_ai.config import Settings
from silabs_ai.engine import SilabsAIEngine
from silabs_ai.retrieval import JsonlKnowledgeRetriever, NullRetriever

import json



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


def test_engine_uses_null_retriever_when_rag_disabled(tmp_path):
    settings = Settings(
        _env_file=None,
        rag_enabled=False,
        knowledge_path=str(tmp_path / "knowledge.jsonl"),
    )
    engine = SilabsAIEngine(settings)

    assert isinstance(engine.retriever, NullRetriever)


def test_engine_builds_jsonl_retriever_when_rag_enabled(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write_jsonl(
        path,
        [
            {
                "text": "UniXpress provides verified academic resources.",
                "source": "silabs://unixpress",
                "verified": True,
            }
        ],
    )
    settings = Settings(
        _env_file=None,
        rag_enabled=True,
        knowledge_path=str(path),
        rag_limit=3,
    )
    engine = SilabsAIEngine(settings)

    assert isinstance(engine.retriever, JsonlKnowledgeRetriever)
    assert engine.retriever.retrieve("academic resources", limit=3)


def test_bm25_title_weighting_breaks_ambiguous_ties(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    _write_jsonl(
        path,
        [
            {
                "title": "General payments",
                "text": "Authentication uses secret keys for API requests. "
                        "Payments can be initialized and verified. "
                        "This document also discusses many unrelated deployment "
                        "and application topics for a long time. " * 8,
                "source": "https://example.com/general",
                "verified": True,
            },
            {
                "title": "Paystack authentication",
                "text": "Use the Paystack secret key to authenticate API requests.",
                "source": "https://github.com/PaystackHQ/documentation/auth",
                "verified": True,
            },
        ],
    )

    retriever = JsonlKnowledgeRetriever(path)
    results = retriever.retrieve(
        "How should a Paystack API secret key be used for authentication?",
        limit=2,
    )

    assert results[0].source == "https://github.com/PaystackHQ/documentation/auth"
