"""Offline English writing analysis, no downloads or remote dictionary service.

Grammar rules intentionally cover high-confidence English constructions.
Spelling uses a bundled English word-frequency corpus; uncommon names, technical
terms, and other languages can be valid even when the dictionary does not know them.
All suggestions require explicit user approval.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import re

WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
GRAMMAR_RULES = (
    (
        "demonstrative-plural",
        re.compile(r"\b(this|that)\s+(sentences|documents|files|results|problems|questions|reports|examples|students|methods)\b", re.I),
        lambda m: ("these" if m.group(1).lower() == "this" else "those") + " " + m.group(2),
        "Use a plural demonstrative with a plural noun.",
    ),
    (
        "demonstrative-singular",
        re.compile(r"\b(these|those)\s+(sentence|document|file|result|problem|question|report|example|student|method)\b", re.I),
        lambda m: ("this" if m.group(1).lower() == "these" else "that") + " " + m.group(2),
        "Use a singular demonstrative with a singular noun.",
    ),
    (
        "doesnt-have",
        re.compile(r"\b(does(?:n't| not))\s+has\b", re.I),
        lambda m: m.group(1) + " have",
        'Use "have" after "does not" or "doesn\'t".',
    ),
    (
        "didnt-go",
        re.compile(r"\b(did(?:n't| not))\s+(went|saw|wrote|ate|ran)\b", re.I),
        lambda m: m.group(1) + " " + {
            "went": "go", "saw": "see", "wrote": "write",
            "ate": "eat", "ran": "run",
        }[m.group(2).lower()],
        'Use the base verb after "did not" or "didn\'t".',
    ),
    (
        "irregular-perfect",
        re.compile(r"\b(has|have|had)\s+(went|wrote|ate|saw)\b", re.I),
        lambda m: m.group(1) + " " + {
            "went": "gone", "wrote": "written",
            "ate": "eaten", "saw": "seen",
        }[m.group(2).lower()],
        "Use the past participle after have/has/had.",
    ),
    (
        "there-is-plural",
        re.compile(r"\bthere is\s+(many|several|numerous|few)\b", re.I),
        lambda m: "there are " + m.group(1),
        "Use 'there are' before an explicitly plural quantity.",
    ),
    (
        "there-are-singular",
        re.compile(r"\bthere are\s+(an?|one)\s+(issue|problem|document|example|reason|way)\b", re.I),
        lambda m: "there is " + m.group(1) + " " + m.group(2),
        "Use 'there is' before a single countable noun.",
    ),
    (
        "uncountable-information",
        re.compile(r"\b(informations|equipments|advices)\b", re.I),
        lambda m: {
            "informations": "information",
            "equipments": "equipment",
            "advices": "advice",
        }[m.group(1).lower()],
        "This noun is normally uncountable in standard English.",
    ),
)

@dataclass(frozen=True)
class Issue:
    category: str
    rule_id: str
    title: str
    message: str
    start: int
    end: int
    original: str
    replacements: list[str]
    confidence: str = "high"

    def json(self) -> dict:
        return asdict(self)


def _preserve_case(original: str, revised: str) -> str:
    if original.isupper():
        return revised.upper()
    if original[:1].isupper():
        return revised[:1].upper() + revised[1:]
    return revised


def _grammar(text: str) -> list[Issue]:
    issues = []
    for rule_id, regex, replace, message in GRAMMAR_RULES:
        for match in regex.finditer(text):
            revised = _preserve_case(match.group(0), replace(match))
            if match.group(0) == revised:
                continue
            issues.append(Issue(
                "grammar", rule_id, "Grammar agreement" if rule_id.startswith("demonstrative") else "Grammar",
                message, match.start(), match.end(), match.group(0), [revised],
            ))
    # Article errors should use narrow, defensible spelling contexts.
    for match in re.finditer(r"\b(a|an)\s+(apple|orange|umbrella|egg|idea|university|uniform|user)\b", text, re.I):
        word = match.group(2).lower()
        expected = "a" if word in {"university", "uniform", "user"} else "an"
        if match.group(1).lower() != expected:
            revised = _preserve_case(match.group(0), expected + " " + match.group(2))
            issues.append(Issue("grammar", "article", "Article agreement",
                "Choose a/an according to the following word's sound.",
                match.start(), match.end(), match.group(0), [revised]))
    return issues


@lru_cache(maxsize=1)
def _english_index():
    from wordfreq import top_n_list
    # Case-insensitive, offline, loaded once per bridge process.
    vocabulary = [
        w for w in top_n_list("en", 80000)
        if w.isascii() and w.isalpha() and 3 <= len(w) <= 28
    ]
    buckets = {}
    for word in vocabulary:
        buckets.setdefault((word[:1], len(word)), []).append(word)
    return set(vocabulary), buckets


@lru_cache(maxsize=2048)
def _spelling_candidates(term: str) -> tuple[str, ...]:
    from rapidfuzz import fuzz, process
    from wordfreq import zipf_frequency
    known, buckets = _english_index()
    if term in known or zipf_frequency(term, "en") > 2.5:
        return ()
    if len(term) < 4 or len(term) > 24:
        return ()
    choices: list[str] = []
    for delta in (-2, -1, 0, 1, 2):
        choices.extend(buckets.get((term[0], len(term) + delta), ()))
    # Avoid best matches from very different spellings.
    found = process.extract(term, choices, scorer=fuzz.ratio,
        limit=12, score_cutoff=65.0)
    ranked = sorted(
        (
            (candidate, score, zipf_frequency(candidate, "en"))
            for candidate, score, _ in found
            if candidate != term
        ),
        key=lambda v: (v[1] + max(0, v[2] - 3) * 3, v[2]),
        reverse=True,
    )
    return tuple(word for word, _, _ in ranked[:4])


def _spelling(text: str) -> list[Issue]:
    from wordfreq import zipf_frequency
    issues = []
    for token in WORD_RE.finditer(text):
        term = token.group()
        # English-only support and proper names should not be silently flagged.
        if len(term) < 4 or len(term) > 24 or term[0].isupper() or "'" in term or "’" in term:
            continue
        lower = term.lower()
        if zipf_frequency(lower, "en") > 2.5:
            continue
        replacements = list(_spelling_candidates(lower))
        if not replacements:
            continue
        issues.append(Issue(
            "spelling", "dictionary-unknown", "Possible spelling issue",
            "The word is uncommon in the offline English dictionary. It may be a valid technical term or name.",
            token.start(), token.end(), term, replacements, "medium",
        ))
        if len(issues) >= 40:
            break
    return issues


def analyse_writing(text: str, *, spelling: bool = True) -> dict:
    if not isinstance(text, str):
        raise ValueError("Writing analysis requires text.")
    if len(text) > 12000:
        raise ValueError("Analyse one passage at a time (12,000 characters maximum).")
    issues = _grammar(text)
    if spelling:
        issues.extend(_spelling(text))
    # Non-overlapping suggestions and stable source offsets.
    result: list[Issue] = []
    for issue in sorted(issues, key=lambda x: (x.start, x.end, x.category)):
        if not result or issue.start >= result[-1].end:
            result.append(issue)
        if len(result) >= 65:
            break
    return {
        "language": "en",
        "engine": "offline-rules-and-word-frequency",
        "issues": [x.json() for x in result],
        "text_length": len(text),
        "limitations": (
            "English-only, suggestive not exhaustive. Unknown terms may be valid, "
            "and grammar rules do not replace a complete language parser."
        ),
    }
