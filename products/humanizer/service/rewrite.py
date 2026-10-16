"""Humanizer rewrite orchestration.

The model adapter is deliberately injected so this product can use the shared
Silabs AI runtime today and a packaged GGUF/llama.cpp runtime later.
"""

from __future__ import annotations

from collections.abc import Callable

from .critic import CriticResult, critique
from .preservation import protect_text, restore_text
from .style_profile import StyleProfile


GenerateFn = Callable[[str], str]


def build_prompt(text: str, profile: StyleProfile) -> str:
    return f"""You are the Silabs Humanizer editing engine.

Rewrite the supplied text naturally while preserving its meaning.
Do not invent facts.
Do not alter protected placeholders.
Do not add citations that were not supplied.
{profile.instruction()}

Text:
{text}

Return only the rewritten text.
"""


def rewrite_text(
    text: str,
    generate: GenerateFn,
    profile: StyleProfile | None = None,
) -> tuple[str, CriticResult]:
    profile = profile or StyleProfile()
    protected = protect_text(text)
    prompt = build_prompt(protected.masked_text, profile)
    candidate = generate(prompt).strip()

    result = critique(
        original=protected.masked_text,
        rewritten=candidate,
        required_tokens=protected.values,
    )

    if not result.passed:
        return text, result

    restored = restore_text(candidate, protected.values)
    return restored, result
