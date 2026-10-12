from __future__ import annotations

import re
from dataclasses import dataclass


_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


@dataclass(frozen=True)
class ResponseContract:
    direct_response: str | None = None
    system_instruction: str | None = None
    category: str | None = None


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _parse_count(value: str) -> int | None:
    value = value.strip().lower()
    if value.isdigit():
        return int(value)
    return _NUMBER_WORDS.get(value)


def contract_for_prompt(prompt: str) -> ResponseContract | None:
    """Resolve deterministic response constraints from an explicit user prompt."""
    text = prompt.strip()
    normalized = re.sub(r"\s+", " ", text).strip()
    lower = normalized.lower()

    if re.fullmatch(
        r"(what is your name\??|what's your name\??|who are you\??)",
        lower,
    ):
        return ResponseContract(
            direct_response=(
                "I am Silabs AI, an AI assistant built by "
                "Simeon's Laboratories and Co Technologies Ltd."
            ),
            category="identity",
        )

    exact_words = re.fullmatch(
        r"(?is)reply with exactly\s+([a-z]+|\d+)\s+words\s*:\s*(.+)",
        normalized,
    )
    if exact_words:
        count = _parse_count(exact_words.group(1))
        requested = exact_words.group(2).strip()
        if count is not None and _word_count(requested) == count:
            return ResponseContract(
                direct_response=requested,
                category="exact_words",
            )

    exact_phrase = re.fullmatch(
        r"(?is)write exactly this phrase and nothing else\s*:\s*(.+)",
        normalized,
    )
    if exact_phrase:
        return ResponseContract(
            direct_response=exact_phrase.group(1).strip(),
            category="exact_phrase",
        )

    instructions: list[str] = []

    word_limit = re.search(
        r"(?i)(?:at most|no more than)\s+(\d+)\s+words",
        normalized,
    )
    if word_limit:
        limit = int(word_limit.group(1))
        instructions.append(
            f"Hard output constraint: answer in no more than {limit} words. "
            "Count carefully before responding."
        )

    if re.search(r"(?i)\bfictional\b", normalized):
        instructions.append(
            "The user explicitly describes an entity or scenario as fictional. "
            "Do not invent real-world records, awards, dates, affiliations, or other "
            "facts for it. Answer briefly and state the fictional status when relevant."
        )

    if instructions:
        return ResponseContract(
            system_instruction=" ".join(instructions),
            category="instruction",
        )

    return None
