"""Curated, synthetic offline lexical QA, not a population accuracy estimate.

Run:
    python -m products.humanizer.tests.language_benchmark

The held-out examples are small, selected to catch regression and protect
academic/British/Nigerian vocabulary. They do not measure performance on
natural unrestricted documents or guarantee grammar correctness.
"""
from __future__ import annotations

import json
from products.humanizer.service.offline_review import analyse_writing

# Tokens in these sentences are deliberately legitimate, including:
# Nigerian English, university contexts, British spellings, scientific terms.
VALID_SAMPLES = {
    "nigerian-english": [
        "The harmattan affected borehole maintenance in Benue.",
        "Students registered for SIWES and submitted their matric details.",
        "Our corpers discussed the NYSC programme in Makurdi.",
        "Farmers sold garri, egusi, suya and amala in the local market.",
        "The okada and keke drivers travelled to the centre.",
        "The LGA organised a sensitisation programme for residents.",
        "The Naira value changed during the project implementation.",
        "Agricultural extension research evaluated biochar and agroforestry.",
        "The Yoruba, Tiv and Idoma language examples remain in the corpus.",
        "WAEC and JAMB registration details were entered into a dataset.",
    ],
    "academic": [
        "The radiometric correction preceded georeferencing in QGIS.",
        "Spatial autocorrelation and multicollinearity were analysed.",
        "Anthropogenic pressure influenced the NDVI trend.",
        "The researchers used PostGIS and geostatistics.",
        "Multivariate modelling was conducted in SPSS and Stata.",
        "A recent study reported heteroscedasticity in the residuals.",
        "The Sentinel imagery was used for landcover classification.",
        "The methodology included georeferenced datasets and metadata.",
        "The analysis measured radiometric and geospatial uncertainty.",
        "The bibliography cited a valid DOI: 10.1234/abcd.9876.",
    ],
    "british-english": [
        "The programme focused on labour productivity.",
        "A colour catalogue described the centre's behaviour.",
        "The organisation will organise student enrolment.",
        "The researcher sought to optimise modelling techniques.",
        "The defence included a discussion of the theatre.",
        "Sensitisation and mobilisation were important to the analysis.",
        "The researchers analysed the local behaviour of the system.",
        "The university issued a licence for the travelling programme.",
        "The team worked to standardise the modelling procedure.",
        "The method was developed to fulfil the project's objectives.",
    ],
    "protected-technical": [
        "The software connects to https://unixpress.com.ng/blog.",
        "The technical paper includes the identifier getServerName42.",
        "The results cited “we should of gone” as a verbatim utterance.",
        "The text contained an inline fragment " + chr(96) + "should of" + chr(96) + " that must not be edited.",
        "The author supplied test@example.com and DOI 10.1016/j.abc.2026.01.",
    ],
}

# Deliberately misspelled lowercase common English words.
TYPO_CASES = {
    "sentnce": "sentence",
    "enviroment": "environment",
    "goverment": "government",
    "recieve": "receive",
    "conculsion": "conclusion",
    "reserach": "research",
}

# Grammar errors that the built-in context-sensitive rules should recognise.
GRAMMAR_CASES = {
    "The study show results.": ("The study show", "The study shows"),
    "The findings suggests improvement.": ("The findings suggests", "The findings suggest"),
    "The analysis have flaws.": ("The analysis have", "The analysis has"),
    "This documents needs attention.": ("This documents", "These documents"),
    "They was ready.": ("They was", "They were"),
    "She don't agree.": ("She don't", "She doesn't"),
    "We should of left.": ("should of", "should have"),
    "A honest reviewer reviewed this.": None,  # not yet supported by narrow rules
}


def run_benchmark() -> dict:
    case_results = []
    for category, sentences in VALID_SAMPLES.items():
        for sentence in sentences:
            issues = analyse_writing(sentence)["issues"]
            spell = [i for i in issues if i["category"] == "spelling"]
            case_results.append({
                "category": category,
                "input": sentence,
                "unexpected_spell": [i["original"] for i in spell],
                "count": len(spell),
            })
    spelling_hits = {}
    for wrong, right in TYPO_CASES.items():
        result = analyse_writing(f"Please review the {wrong} carefully.")
        proposed = [item["replacements"] for item in result["issues"]
                    if item["original"] == wrong and item["category"] == "spelling"]
        spelling_hits[wrong] = right in (proposed[0] if proposed else [])
    grammar_hits = {}
    for sample, expected in GRAMMAR_CASES.items():
        if expected is None:
            continue
        result = analyse_writing(sample, spelling=False)
        grammar_hits[sample] = any(
            issue["original"] == expected[0] and expected[1] in issue["replacements"]
            for issue in result["issues"]
        )
    sample_total = len(case_results)
    samples_flagged = sum(1 for item in case_results if item["count"] > 0)
    return {
        "name": "curated-academic-Nigerian-English-smoke-v1",
        "not_representative": True,
        "valid_sample_count": sample_total,
        "valid_samples_flagged": samples_flagged,
        "sample_level_false_positive_rate": round(samples_flagged / sample_total, 4),
        "spelling_typo_examples": spelling_hits,
        "typo_recall_on_selected_examples": round(
            sum(spelling_hits.values()) / len(spelling_hits), 4,
        ),
        "grammar_examples": grammar_hits,
        "grammar_coverage_on_selected_examples": round(
            sum(grammar_hits.values()) / len(grammar_hits), 4,
        ),
        "flagged_valid_examples": [item for item in case_results if item["count"]],
    }


if __name__ == "__main__":
    report = run_benchmark()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["valid_samples_flagged"] > 0 or (
        report["typo_recall_on_selected_examples"] < 0.65
        or report["grammar_coverage_on_selected_examples"] < 1
    ):
        raise SystemExit("Curated language smoke benchmark missed its quality gates.")
