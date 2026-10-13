from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_'-]*")


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str | None = None
    score: float | None = None


@dataclass(frozen=True)
class KnowledgeRecord:
    text: str
    source: str
    title: str | None = None
    verified: bool = True

    @classmethod
    def from_mapping(cls, data: dict) -> "KnowledgeRecord":
        text = str(data.get("text", "")).strip()
        source = str(data.get("source", "")).strip()
        if not text:
            raise ValueError("Knowledge record requires non-empty text")
        if not source:
            raise ValueError("Knowledge record requires non-empty source")

        title = data.get("title")
        title = str(title).strip() if title is not None else None
        verified = bool(data.get("verified", True))
        return cls(
            text=text,
            source=source,
            title=title or None,
            verified=verified,
        )


class Retriever(Protocol):
    def retrieve(self, query: str, *, limit: int = 4) -> list[RetrievedChunk]:
        ...


class NullRetriever:
    """Default retriever when RAG is disabled."""

    def retrieve(self, query: str, *, limit: int = 4) -> list[RetrievedChunk]:
        del query, limit
        return []


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


class JsonlKnowledgeRetriever:
    """Small dependency-free retriever for verified local knowledge.

    It intentionally uses lexical TF-IDF-style scoring rather than embeddings.
    This gives Silabs AI a deterministic RAG baseline that works offline and is
    easy to regression-test. A semantic/vector backend can later implement the
    same Retriever protocol without changing the engine.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        verified_only: bool = True,
        min_score: float = 0.0,
    ) -> None:
        self.path = Path(path)
        self.verified_only = verified_only
        self.min_score = min_score
        self._records = self._load_records()
        self._document_term_counts = self._build_document_term_counts()
        self._document_frequency = self._build_document_frequency()

    def _load_records(self) -> list[KnowledgeRecord]:
        if not self.path.exists():
            return []

        records: list[KnowledgeRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                raw = raw.strip()
                if not raw:
                    continue

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON at {self.path}:{line_number}"
                    ) from exc

                record = KnowledgeRecord.from_mapping(data)
                if self.verified_only and not record.verified:
                    continue
                records.append(record)

        return records

    def _build_document_term_counts(self) -> list[Counter[str]]:
        counts: list[Counter[str]] = []
        for record in self._records:
            tokens = _tokens(record.text)
            if record.title:
                tokens.extend(_tokens(record.title))
            counts.append(Counter(tokens))
        return counts

    def _build_document_frequency(self) -> Counter[str]:
        frequency: Counter[str] = Counter()
        for counts in self._document_term_counts:
            frequency.update(counts.keys())
        return frequency

    def _score(self, query_tokens: list[str], counts: Counter[str]) -> float:
        if not query_tokens:
            return 0.0

        total_docs = max(len(self._records), 1)
        score = 0.0

        for token in set(query_tokens):
            tf = counts[token]
            if tf == 0:
                continue
            df = self._document_frequency.get(token, 0)
            idf = math.log((1 + total_docs) / (1 + df)) + 1.0
            score += (1.0 + math.log(tf)) * idf

        return score

    def retrieve(self, query: str, *, limit: int = 4) -> list[RetrievedChunk]:
        if limit <= 0:
            return []

        query_tokens = _tokens(query)
        ranked: list[tuple[float, KnowledgeRecord]] = []

        for record, counts in zip(self._records, self._document_term_counts):
            score = self._score(query_tokens, counts)
            if score > self.min_score:
                ranked.append((score, record))

        ranked.sort(key=lambda item: (-item[0], item[1].source, item[1].text))

        return [
            RetrievedChunk(
                text=record.text,
                source=record.source,
                score=round(score, 6),
            )
            for score, record in ranked[:limit]
        ]
