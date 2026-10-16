"""Deterministic first-pass protection and rewrite checks."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CriticResult:
    passed: bool
    issues: list[str]


def critique(original: str, rewritten: str, required_tokens: dict[str, str]) -> CriticResult:
    issues: list[str] = []

    if not rewritten.strip():
        issues.append("Rewrite is empty.")

    if original.strip() == rewritten.strip():
        issues.append("Rewrite made no meaningful change.")

    for token in required_tokens:
        count = rewritten.count(token)
        if count != 1:
            issues.append(f"Protected token must occur once: {token} (got {count})")

    # Numeric values are always protected in the input. New unprotected digits
    # introduced by the model may be invented facts, or altered placeholders.
    candidate_without_tokens = rewritten
    for token in required_tokens:
        candidate_without_tokens = candidate_without_tokens.replace(token, "")
    if re.search(r"\d", candidate_without_tokens):
        issues.append("New unprotected digits detected in rewrite.")

    return CriticResult(passed=not issues, issues=issues)
