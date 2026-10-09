from silabs_ai.prompting import ensure_system_message


def test_custom_system_prompt_is_additive_to_base_contract():
    messages = [
        {"role": "system", "content": "Act as a concise mathematics tutor."},
        {"role": "user", "content": "Explain fractions."},
    ]

    result = ensure_system_message(
        messages,
        "BASE SAFETY CONTRACT",
    )

    assert result[0]["role"] == "system"
    assert result[0]["content"].startswith("BASE SAFETY CONTRACT")
    assert "Additional application instructions:" in result[0]["content"]
    assert "concise mathematics tutor" in result[0]["content"]


def test_base_contract_is_not_duplicated():
    messages = [
        {"role": "system", "content": "BASE SAFETY CONTRACT"},
        {"role": "user", "content": "Hello"},
    ]

    result = ensure_system_message(messages, "BASE SAFETY CONTRACT")

    assert result[0]["content"] == "BASE SAFETY CONTRACT"
    assert result[0]["content"].count("BASE SAFETY CONTRACT") == 1
