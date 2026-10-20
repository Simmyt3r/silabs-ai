"""Private local similarity check against explicitly selected reference files.

This is not an internet plagiarism detector. It detects exact normalized
8-word sequences, reports matched coverage and source excerpts, and never
labels authorship, misconduct, or originality.
"""
from __future__ import annotations

import re
from pathlib import Path
from .document_parser import parse_document

TOKEN = re.compile(r"[\w']+", re.UNICODE)
SHINGLE = 8
MAX_SOURCES = 15
MAX_SOURCE_BYTES = 12 * 1024 * 1024
MAX_WORDS_PER_FILE = 60_000


def _words(text: str) -> list[str]:
    return [match.group().casefold() for match in TOKEN.finditer(text)]


def _windows(words: list[str], length: int = SHINGLE):
    for index in range(max(0, len(words) - length + 1)):
        yield index, tuple(words[index:index + length])


def _source_text(path: Path) -> str:
    parsed = parse_document(path)
    return "\n".join(block.text for block in parsed.blocks if block.text.strip())


def compare_local_sources(
    draft: str, sources: list[str], *, source_document: str | None = None
) -> dict:
    if not isinstance(draft, str) or not draft.strip():
        raise ValueError("Choose text to compare before running source similarity.")
    if not isinstance(sources, list) or not 1 <= len(sources) <= MAX_SOURCES:
        raise ValueError(f"Select 1-{MAX_SOURCES} local reference documents.")
    words = _words(draft)
    if len(words) > MAX_WORDS_PER_FILE:
        raise ValueError("Document too long for this local comparison.")
    if len(words) < SHINGLE:
        return {
            "scope": "selected-local-files-only",
            "status": "too-short",
            "source_count": 0,
            "draft_words": len(words),
            "coverage_percent": 0,
            "sources": [],
            "explanation": f"Comparison requires at least {SHINGLE} words.",
        }

    draft_windows = {window for _, window in _windows(words)}
    total_covered = set()
    reports = []
    seen = set()
    self_path = Path(source_document).resolve() if source_document else None

    for raw_path in sources:
        if not isinstance(raw_path, str):
            raise ValueError("Reference paths must be local filenames.")
        path = Path(raw_path).expanduser().resolve()
        if self_path is not None and path == self_path:
            raise ValueError("A document cannot be compared with itself.")
        if path in seen:
            continue
        seen.add(path)
        if not path.is_file() or path.suffix.lower() not in {".docx", ".txt", ".md"}:
            raise ValueError("Reference must be an existing DOCX, TXT or Markdown document.")
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError(f"Reference file is too large: {path.name}")
        source_words = _words(_source_text(path))
        if len(source_words) > MAX_WORDS_PER_FILE:
            raise ValueError(f"Reference has too many words: {path.name}")
        ref_windows = {}
        for at, shingle in _windows(source_words):
            if shingle in draft_windows and shingle not in ref_windows:
                ref_windows[shingle] = at
        covered = set()
        excerpts = []
        for at, shingle in _windows(words):
            if shingle not in ref_windows:
                continue
            interval = range(at, at + SHINGLE)
            newly_matched = any(i not in covered for i in interval)
            covered.update(interval)
            total_covered.update(interval)
            if newly_matched and len(excerpts) < 5:
                src_at = ref_windows[shingle]
                start = max(0, src_at - 6)
                stop = min(len(source_words), src_at + SHINGLE + 6)
                excerpts.append({
                    "draft_excerpt": " ".join(words[max(0, at-3):min(len(words), at+SHINGLE+3)]),
                    "source_excerpt": " ".join(source_words[start:stop]),
                })
        if covered:
            reports.append({
                "name": path.name,
                "matched_words": len(covered),
                "draft_coverage_percent": round(len(covered) * 100 / len(words), 1),
                "match_excerpts": excerpts,
            })

    reports.sort(key=lambda x: x["matched_words"], reverse=True)
    return {
        "scope": "selected-local-files-only",
        "status": "compared",
        "source_count": len(seen),
        "draft_words": len(words),
        "coverage_percent": round(len(total_covered) * 100 / len(words), 1),
        "sources": reports,
        "explanation": (
            "Coverage means exact matching word sequences against ONLY the files selected. "
            "It is not a plagiarism verdict, cannot detect paraphrases reliably, "
            "and does not search the internet or commercial databases."
        ),
    }
