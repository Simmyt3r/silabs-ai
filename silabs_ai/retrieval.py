from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str | None = None
    score: float | None = None


class Retriever(Protocol):
    def retrieve(self, query: str, *, limit: int = 4) -> list[RetrievedChunk]:
        ...


class NullRetriever:
    """Default retriever until a product supplies a real RAG backend."""

    def retrieve(self, query: str, *, limit: int = 4) -> list[RetrievedChunk]:
        del query, limit
        return []
