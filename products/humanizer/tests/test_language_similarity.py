from docx import Document
import pytest

from products.humanizer.service.desktop_bridge import process
from products.humanizer.service.offline_review import analyse_writing
from products.humanizer.service.local_similarity import compare_local_sources


def test_grammar_reports_specific_contextual_errors_with_offsets():
    text = "This sentences doesn't has clear details. An university sent several reports."
    report = analyse_writing(text, spelling=False)
    suggestions = [item for item in report["issues"] if item["category"] == "grammar"]
    assert any(i["original"] == "This sentences" and i["replacements"] == ["These sentences"]
               and text[i["start"]:i["end"]] == i["original"] for i in suggestions)
    assert any("have" in i["replacements"][0] for i in suggestions)
    assert any(i["original"] == "An university" and i["replacements"] == ["A university"]
               for i in suggestions)


def test_english_spelling_suggests_common_correction_and_preserves_original():
    text = "Please check the sentnce before export."
    report = analyse_writing(text)
    spelling = [i for i in report["issues"] if i["category"] == "spelling"]
    assert any(i["original"] == "sentnce" and "sentence" in i["replacements"]
               for i in spelling)
    assert text == "Please check the sentnce before export."


def test_non_english_or_proper_names_are_not_forcibly_autocorrected():
    text = "Qwen Silabs Makurdi Yoruba Søren."
    report = analyse_writing(text)
    assert not [issue for issue in report["issues"] if issue["category"] == "spelling"]


def test_local_source_comparison_reports_matched_coverage_without_misconduct_verdict(tmp_path):
    draft = (
        "The satellite image analysis identified a range of temporary settlements "
        "that were previously not visible in historical observations. Further validation is required."
    )
    reference = tmp_path / "source.docx"
    doc = Document()
    doc.add_paragraph(
        "Recent monitoring used many different techniques. "
        "The satellite image analysis identified a range of temporary settlements "
        "that were previously not visible in historical observations. "
        "The methodology was assessed separately."
    )
    doc.save(reference)
    result = compare_local_sources(draft, [str(reference)])
    assert result["scope"] == "selected-local-files-only"
    assert result["source_count"] == 1
    assert result["coverage_percent"] > 25
    assert result["sources"][0]["name"] == "source.docx"
    assert result["sources"][0]["match_excerpts"]
    assert "not a plagiarism verdict" in result["explanation"]


def test_local_source_comparison_checks_current_draft_and_validates_source(tmp_path):
    essay = tmp_path / "essay.txt"
    essay.write_text("Different original text stored here.", encoding="utf-8")
    reference = tmp_path / "source.txt"
    matching = "Satellite observations require careful manual checking before final reporting."
    reference.write_text(matching, encoding="utf-8")
    doc = process({"action": "open", "path": str(essay)})
    report = process({
        "action": "compare_local_sources",
        "path": str(essay),
        "fingerprint": doc["fingerprint"],
        "revisions": {"0": matching},
        "sources": [str(reference)],
    })
    assert report["coverage_percent"] == 100
    with pytest.raises(ValueError, match="cannot be compared with itself"):
        process({
            "action": "compare_local_sources", "path": str(essay),
            "fingerprint": doc["fingerprint"],
            "revisions": {}, "sources": [str(essay)],
        })


def test_source_comparison_does_not_claim_originality_from_empty_results(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_text("A completely unrelated set of common words is written here.",
                      encoding="utf-8")
    result = compare_local_sources(
        "Satellite imagery revealed changing vegetation across several local districts.",
        [str(source)],
    )
    assert result["coverage_percent"] == 0
    assert result["sources"] == []
    assert "does not search the internet" in result["explanation"]


def test_grammar_and_spelling_still_work_in_bridge_json():
    outcome = process({"action": "analyse_writing", "text": "This sentences contains a sentnce."})
    assert outcome["language"] == "en"
    assert any(x["category"] == "grammar" for x in outcome["issues"])
