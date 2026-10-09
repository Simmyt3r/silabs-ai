from pathlib import Path

from evaluation.promotion_gate import assess
from evaluation.run_eval import judge, load_cases, resolve_settings


def test_exact_judge_is_case_insensitive():
    passed, failures = judge({"exact": "SELECT"}, "select")
    assert passed is True
    assert failures == []


def test_regex_and_word_limit():
    passed, failures = judge(
        {"must_match": ["^carbon dioxide[.!]?$"], "max_words": 3},
        "Carbon dioxide.",
    )
    assert passed is True
    assert failures == []


def test_model_argument_disables_default_local_base_for_remote_id():
    settings = resolve_settings("example/other-model", offline=False)
    assert settings.model_id == "example/other-model"
    assert settings.model_path is None


def test_local_candidate_is_selected(tmp_path):
    checkpoint = tmp_path / "candidate"
    checkpoint.mkdir()
    settings = resolve_settings(str(checkpoint), offline=True)
    assert settings.model_path == str(checkpoint)
    assert settings.allow_remote_model_download is False


def test_local_adapter_uses_base_model_and_adapter_path(tmp_path):
    checkpoint = tmp_path / "adapter"
    checkpoint.mkdir()
    (checkpoint / "adapter_config.json").write_text("{}", encoding="utf-8")

    settings = resolve_settings(str(checkpoint), offline=True)

    assert settings.adapter_path == str(checkpoint)
    assert settings.model_path == "models/base/SmolLM2-360M-Instruct"
    assert settings.allow_remote_model_download is False



def test_extended_evaluation_suite_is_valid_and_unique():
    cases = load_cases(Path("evaluation/cases_extended.jsonl"))
    ids = [case["id"] for case in cases]

    assert len(cases) == 50
    assert len(ids) == len(set(ids))



def test_promotion_gate_accepts_improvement_without_regressions():
    passed, reasons = assess(
        {
            "baseline_score": 0.90,
            "candidate_score": 0.95,
            "score_delta": 0.05,
            "regressions": [],
        }
    )
    assert passed is True
    assert reasons == []


def test_promotion_gate_rejects_regression():
    passed, reasons = assess(
        {
            "baseline_score": 0.90,
            "candidate_score": 0.95,
            "score_delta": 0.05,
            "regressions": [{"id": "math_add"}],
        }
    )
    assert passed is False
    assert any("regressions" in reason for reason in reasons)



def test_promotion_gate_rejects_candidate_below_absolute_threshold():
    passed, reasons = assess(
        {
            "baseline_score": 0.70,
            "candidate_score": 0.75,
            "score_delta": 0.05,
            "regressions": [],
        },
        min_candidate_score=0.80,
    )
    assert passed is False
    assert any("candidate score" in reason for reason in reasons)



def test_safety_evaluation_suite_is_valid_and_unique():
    cases = load_cases(Path("evaluation/cases_safety.jsonl"))
    ids = [case["id"] for case in cases]

    assert len(cases) == 12
    assert len(ids) == len(set(ids))
    assert all(case.get("category", "").startswith("safety_") for case in cases)
