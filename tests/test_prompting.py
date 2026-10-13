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


def test_retrieved_context_instructs_source_citations():
    from silabs_ai.prompting import build_chat_messages

    messages = build_chat_messages(
        "What is the fact?",
        retrieved_context=[
            "[S1] Source: source://alpha\nAlpha is verified.",
            "[S2] Source: source://beta\nBeta is verified.",
        ],
    )

    user = messages[-1]["content"]
    assert "[S1]" in user
    assert "[S2]" in user
    assert "cite its context label inline" in user
    assert "never invent a citation" in user
