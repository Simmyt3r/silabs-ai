from silabs_ai.engine import enforce_source_citations
from silabs_ai.retrieval import RetrievedChunk


def _sources():
    return [
        RetrievedChunk(text="Fact one", source="source://one", score=3.0, citation="S1"),
        RetrievedChunk(text="Fact two", source="source://two", score=2.0, citation="S2"),
    ]


def test_keeps_valid_citation_without_repair():
    text, repaired = enforce_source_citations("Supported claim [S2].", _sources())
    assert text == "Supported claim [S2]."
    assert repaired is False


def test_adds_top_source_when_model_omits_citation():
    text, repaired = enforce_source_citations("Supported claim.", _sources())
    assert text.endswith("[S1]")
    assert repaired is True


def test_removes_unknown_label_and_adds_valid_source():
    text, repaired = enforce_source_citations("Supported claim [S9].", _sources())
    assert "[S9]" not in text
    assert text.endswith("[S1]")
    assert repaired is True


def test_does_not_change_text_without_sources():
    text, repaired = enforce_source_citations("General response.", [])
    assert text == "General response."
    assert repaired is False
