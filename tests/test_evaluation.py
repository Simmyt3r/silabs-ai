from evaluation.run_eval import judge, resolve_settings


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
