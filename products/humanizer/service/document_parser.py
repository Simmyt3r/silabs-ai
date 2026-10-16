"""Document parsing contracts for the offline Humanizer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx"}


@dataclass
class DocumentBlock:
    index: int
    kind: str
    text: str
    style: str | None = None


@dataclass
class ParsedDocument:
    path: Path
    blocks: list[DocumentBlock]


def parse_plain_text(path: str | Path) -> ParsedDocument:
    source = Path(path)
    if source.suffix.lower() not in {".txt", ".md"}:
        raise ValueError(f"Unsupported plain-text format: {source.suffix}")

    text = source.read_text(encoding="utf-8")
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    blocks = [
        DocumentBlock(index=i, kind="paragraph", text=paragraph)
        for i, paragraph in enumerate(paragraphs)
    ]
    return ParsedDocument(path=source, blocks=blocks)


def parse_document(path: str | Path) -> ParsedDocument:
    source = Path(path)
    suffix = source.suffix.lower()

    if suffix in {".txt", ".md"}:
        return parse_plain_text(source)

    if suffix == ".docx":
        raise NotImplementedError("DOCX parser is the next implementation step.")

    raise ValueError(f"Unsupported document format: {suffix}")
