"""Word run-aware replacements that preserve styling of unchanged text.

We only operate on ordinary w:r text nodes. Paragraphs containing fields,
inline images, hyperlink markup or non-text runs remain read-only. Replacements
use the nearest run's style while untouched text remains in its original run.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from bisect import bisect_right


def replace_run_text(paragraph, replacement: str) -> None:
    runs = paragraph.runs
    if not runs:
        raise ValueError("Cannot edit a paragraph without a text run.")
    texts = [r.text for r in runs]
    original = "".join(texts)
    if not original:
        raise ValueError("Cannot edit an empty paragraph.")
    if original == replacement:
        return
    boundaries = [0]
    for value in texts:
        boundaries.append(boundaries[-1] + len(value))
    result: list[list[str]] = [[] for _ in runs]

    def owner(offset: int) -> int:
        # Insertion at a formatting boundary inherits the preceding run
        # when available. Unchanged characters keep their original run.
        return min(len(runs) - 1, max(0, bisect_right(boundaries, max(0, offset)) - 1))

    operations = SequenceMatcher(None, original, replacement, autojunk=False).get_opcodes()
    for op, i1, i2, j1, j2 in operations:
        if op == "equal":
            for idx in range(i1, i2):
                result[owner(idx)].append(original[idx])
        elif op in {"insert", "replace"}:
            target = owner(i1 - 1 if i1 else i1)
            result[target].append(replacement[j1:j2])
        # Delete: remove those characters from the corresponding runs.
    for run, fragments in zip(runs, result):
        run.text = "".join(fragments)
