"""Protected-content handling for Silabs Humanizer."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProtectedText:
    masked_text: str
    values: dict[str, str]


_PATTERNS: tuple[tuple[str, str], ...] = (
    ("URL", r"https?://[^\s)\]>]+"),
    ("DOI", r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b"),
    ("CITATION", r"\([A-Z][A-Za-z'’.-]+(?:\s+et\s+al\.)?,?\s+\d{4}[a-z]?\)"),
    ("PERCENT", r"\b\d+(?:\.\d+)?%"),
    ("NUMBER", r"\b\d+(?:\.\d+)?\b"),
)


def protect_text(text: str) -> ProtectedText:
    values: dict[str, str] = {}
    masked = text

    for label, pattern in _PATTERNS:
        counter = 0

        def replace(match: re.Match[str]) -> str:
            nonlocal counter
            counter += 1
            token = f"__{label}_{counter:04d}__"
            values[token] = match.group(0)
            return token

        masked = re.sub(pattern, replace, masked, flags=re.IGNORECASE)

    return ProtectedText(masked_text=masked, values=values)


def restore_text(text: str, values: dict[str, str]) -> str:
    restored = text
    for token, value in values.items():
        restored = restored.replace(token, value)
    return restored


def missing_tokens(text: str, values: dict[str, str]) -> list[str]:
    return [token for token in values if token not in text]
