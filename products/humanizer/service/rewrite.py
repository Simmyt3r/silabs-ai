"""Conservative offline rewrite orchestration for the Humanizer product.

Model output is a proposed revision, never a verified factual correction.
"""
from __future__ import annotations

from collections.abc import Callable

from .critic import CriticResult, critique
from .preservation import protect_text, restore_text
from .style_profile import StyleProfile


GenerateFn = Callable[[str], str]

_MODE_INSTRUCTIONS = {
    "natural": "Improve sentence rhythm and natural flow. Remove formulaic phrasing without adding information.",
    "academic": "Use clear formal academic prose; avoid inflated jargon and preserve methodological precision.",
    "professional": "Use concise, professional workplace language with direct sentences.",
    "simplify": "Make the text easier to understand while preserving every important qualification.",
    "grammar": "Correct grammar, spelling and punctuation only. Minimise changes to diction and sentence structure.",
    "shorten": "Remove repetition and unnecessary words while preserving the argument and all essential details.",
    "expand": "Clarify relationships using only facts already in the supplied text. Do not add evidence, examples, statistics or claims.",
}


def build_prompt(text: str, profile: StyleProfile) -> str:
    instruction = _MODE_INSTRUCTIONS.get(profile.mode)
    if instruction is None:
        raise ValueError(f"Unsupported Humanizer mode: {profile.mode}")
    return f"""You are the Silabs Humanizer editing engine.

Task: {instruction}
Preserve the author's intended meaning, caveats and all verifiable details.
Do not invent facts or fabricate sources.
Never change, reformat, remove or duplicate any protected __SILABS_KEEP_0001__ style placeholder.
Treat all protected placeholders as opaque text and copy each exactly once.
Do not add facts, years, percentages or citations not found in the original.
Do not add headings, meta-comments or editing instructions to the output.
Return only the improved wording, nothing else.
{profile.instruction()}

Text:
{text}"""


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
