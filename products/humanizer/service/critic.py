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

    # Small local models occasionally echo prompt instructions, which must
    # never be offered as an edit (observed in desktop acceptance testing).
    if re.search(r"(?im)^\\s*(?:Return only the rewritten text\\.?|Task:|Rewrite mode:|Text:|You are the Silabs Humanizer editing engine\\.?|<\\|im_start\\|>)\\s*$", rewritten):
        issues.append("Model echoed editing instructions instead of providing a clean revision.")

    for token in required_tokens:
        count = rewritten.count(token)
        if count != 1:
            issues.append(f"Protected token must occur once: {token} (got {count})")

    # Numeric claims stay protected. Structural list numbering (1. 2. etc.)
    # is not a factual claim and should not block a legitimate document edit.
    candidate_without_tokens = rewritten
    for token in required_tokens:
        candidate_without_tokens = candidate_without_tokens.replace(token, "")
    candidate_without_tokens = re.sub(r"(?m)^\\s{0,8}\\d{1,2}[.)]\\s+", "", candidate_without_tokens)
    if re.search(r"\\d", candidate_without_tokens):
        issues.append("The suggestion introduces unverified numeric content.")

    return CriticResult(passed=not issues, issues=issues)
