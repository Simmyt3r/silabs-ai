"""Reversible protected-content masking for offline document rewriting.

Only a conservative set of patterns is covered. Preservation checks are not
a substitute for reviewing factual meaning before accepting a rewrite.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProtectedText:
    masked_text: str
    values: dict[str, str]


# Ordering matters. Citation patterns run before generic numbers so names and
# publication years remain together. A single source-text pass avoids ever
# matching numbers inside generated placeholders.
_PATTERNS: tuple[tuple[str, str], ...] = (
    ("URL", r"https?://[^\s<>\]\)]+"),
    ("DOI", r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b"),
    (
        "CITATION",
        r"\([A-Z][^()]{0,110}?,?\s+\d{4}[a-z]?(?:;\s*[A-Z][^()]{0,110}?,?\s+\d{4}[a-z]?)*\)"
        r"|"
        r"\b[A-Z][A-Za-z'’.-]+(?:\s+(?:&|and)\s+[A-Z][A-Za-z'’.-]+|\s+et\s+al\.)?"
        r"\s*\(\d{4}[a-z]?\)",
    ),
    ("PERCENT", r"(?<!\w)\d+(?:[.,]\d+)?%"),
    ("NUMBER", r"(?<![\w])\d+(?:[.,]\d+)*(?!\w)"),
)
_COMBINED = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in _PATTERNS),
    re.IGNORECASE,
)


def protect_text(text: str) -> ProtectedText:
    values: dict[str, str] = {}
    prefix = "__SILABS_KEEP_"
    while prefix in text:
        prefix = "_" + prefix
    pieces: list[str] = []
    previous = 0
    for match in _COMBINED.finditer(text):
        pieces.append(text[previous:match.start()])
        token = f"{prefix}{len(values) + 1:04d}__"
        values[token] = match.group(0)
        pieces.append(token)
        previous = match.end()
    pieces.append(text[previous:])
    return ProtectedText(masked_text="".join(pieces), values=values)


def restore_text(text: str, values: dict[str, str]) -> str:
    restored = text
    for token, value in values.items():
        restored = restored.replace(token, value)
    return restored


def missing_tokens(text: str, values: dict[str, str]) -> list[str]:
    return [token for token in values if text.count(token) != 1]
