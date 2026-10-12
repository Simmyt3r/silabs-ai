from silabs_ai.config import Settings
from silabs_ai.engine import SilabsAIEngine
from silabs_ai.response_contracts import contract_for_prompt


def offline_settings() -> Settings:
    return Settings(
        _env_file=None,
        model_path="models/definitely-not-present",
        allow_remote_model_download=False,
        enable_guardrails=True,
    )


def test_identity_contract_is_deterministic():
    contract = contract_for_prompt("What is your name?")
    assert contract is not None
    assert contract.direct_response is not None
    assert "Silabs AI" in contract.direct_response


def test_exact_word_contract_returns_requested_phrase():
    contract = contract_for_prompt(
        "Reply with exactly two words: machine learning"
    )
    assert contract is not None
    assert contract.direct_response == "machine learning"


def test_exact_word_contract_rejects_mismatched_count():
    contract = contract_for_prompt(
        "Reply with exactly two words: artificial intelligence system"
    )
    assert contract is None


def test_word_limit_creates_hard_instruction():
    contract = contract_for_prompt(
        "Define a computer in one sentence of at most 15 words."
    )
    assert contract is not None
    assert contract.direct_response is None
    assert "15 words" in contract.system_instruction


def test_fictional_prompt_creates_no_invention_instruction():
    contract = contract_for_prompt(
        "What year did the fictional scientist Dr. Example win the Nobel Prize?"
    )
    assert contract is not None
    assert "fictional" in contract.system_instruction.lower()
    assert "do not invent" in contract.system_instruction.lower()


def test_identity_contract_returns_before_model_load():
    engine = SilabsAIEngine(offline_settings())
    result = engine.chat("What is your name?")

    assert result.finish_reason == "contract"
    assert "Silabs AI" in result.text
    assert engine.loaded is False


def test_exact_word_contract_returns_before_model_load():
    engine = SilabsAIEngine(offline_settings())
    result = engine.chat(
        "Reply with exactly two words: machine learning"
    )

    assert result.finish_reason == "contract"
    assert result.text == "machine learning"
    assert engine.loaded is False
