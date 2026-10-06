from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class DatasetFormatError(ValueError):
    pass


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def normalize_record(record: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize common instruction-data schemas to role/content messages."""
    raw_messages = record.get("messages")
    if isinstance(raw_messages, list) and raw_messages:
        messages: list[dict[str, str]] = []
        for item in raw_messages:
            if not isinstance(item, dict):
                raise DatasetFormatError("messages entries must be objects")
            role = _text(item.get("role"))
            content = _text(item.get("content"))
            if role not in {"system", "user", "assistant"} or not content:
                raise DatasetFormatError("invalid role/content in messages")
            messages.append({"role": role, "content": content})
        if messages[-1]["role"] != "assistant":
            raise DatasetFormatError("last message must be assistant")
        return messages

    system = _text(record.get("system"))
    pairs = [
        ("instruction", "output"),
        ("prompt", "response"),
        ("question", "answer"),
        ("input", "output"),
    ]
    for left, right in pairs:
        prompt = _text(record.get(left))
        answer = _text(record.get(right))
        if prompt and answer:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ])
            return messages

    raise DatasetFormatError(
        "record must contain messages or a supported prompt/answer field pair"
    )


def iter_jsonl(path: str | Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetFormatError(
                    f"{path}:{line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(item, dict):
                raise DatasetFormatError(f"{path}:{line_number}: expected JSON object")
            yield line_number, item


def load_messages(path: str | Path) -> list[list[dict[str, str]]]:
    rows = []
    for line_number, record in iter_jsonl(path):
        try:
            rows.append(normalize_record(record))
        except DatasetFormatError as exc:
            raise DatasetFormatError(f"{path}:{line_number}: {exc}") from exc
    return rows
