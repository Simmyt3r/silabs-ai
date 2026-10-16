"""Deterministic first-pass output checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CriticResult:
    passed: bool
    issues: list[str]


def critique(original: str, rewritten: str, required_tokens: dict[str, str]) -> CriticResult:
    issues: list[str] = []

    for token in required_tokens:
        if token not in rewritten:
            issues.append(f"Protected token missing: {token}")

    if not rewritten.strip():
        issues.append("Rewrite is empty.")

    if original.strip() == rewritten.strip():
        issues.append("Rewrite made no meaningful change.")

    return CriticResult(passed=not issues, issues=issues)
