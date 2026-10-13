from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse


_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_'-]*")


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str | None = None
    score: float | None = None
    citation: str | None = None


@dataclass(frozen=True)
class KnowledgeRecord:
    text: str
    source: str
    title: str | None = None
    verified: bool = True
    repository: str | None = None
    source_scope: str | None = None
    authority: str | None = None

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
        repository = data.get("repository")
        repository = str(repository).strip() if repository is not None else None
        source_scope = data.get("source_scope")
        source_scope = str(source_scope).strip() if source_scope is not None else None
        authority = data.get("authority")
        authority = str(authority).strip() if authority is not None else None
        return cls(
            text=text,
            source=source,
            title=title or None,
            verified=verified,
            repository=repository or None,
            source_scope=source_scope or None,
            authority=authority or None,
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
        self._title_term_counts = self._build_title_term_counts()
        self._document_lengths = [sum(counts.values()) for counts in self._document_term_counts]
        self._average_document_length = (
            sum(self._document_lengths) / len(self._document_lengths)
            if self._document_lengths
            else 1.0
        )
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

    def _build_title_term_counts(self) -> list[Counter[str]]:
        return [
            Counter(_tokens(record.title or ""))
            for record in self._records
        ]

    def _build_document_frequency(self) -> Counter[str]:
        frequency: Counter[str] = Counter()
        for counts in self._document_term_counts:
            frequency.update(counts.keys())
        return frequency

    def _score(
        self,
        query_tokens: list[str],
        counts: Counter[str],
        title_counts: Counter[str],
        document_length: int,
        record: KnowledgeRecord,
    ) -> float:
        if not query_tokens:
            return 0.0

        total_docs = max(len(self._records), 1)
        unique_query = set(query_tokens)
        score = 0.0
        matched = 0

        # BM25 keeps long documentation chunks from winning simply because
        # they contain more occurrences of common query terms.
        k1 = 1.5
        b = 0.75
        avgdl = max(self._average_document_length, 1.0)
        length_norm = 1.0 - b + b * (document_length / avgdl)

        for token in unique_query:
            tf = counts[token]
            if tf == 0:
                continue

            matched += 1
            df = self._document_frequency.get(token, 0)
            idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
            bm25 = idf * ((tf * (k1 + 1.0)) / (tf + k1 * length_norm))

            # Titles are concise document labels and carry much stronger
            # intent than incidental occurrences inside a long documentation
            # chunk.
            title_bonus = 1.75 * idf if title_counts[token] else 0.0
            score += bm25 + title_bonus

        # Prefer documents covering more of the user's distinct terms. This
        # helps the correct source move from rank 2/3 to rank 1 without
        # sacrificing the strong lexical recall of the baseline.
        if unique_query:
            score += 2.0 * (matched / len(unique_query))

        # Prefer the canonical named source rather than an integration page
        # that merely mentions the same technology in its path or title.
        #
        # Repository-backed docs use the registered repository identity. Web
        # docs use the hostname. For older/minimal records, GitHub owner/repo
        # is inferred from the source URL. Page-path terms are intentionally
        # excluded so /guides/tailwind-v3-css does not make nextjs.org look
        # like Tailwind's canonical documentation.
        canonical_identity = ""
        if record.repository:
            canonical_identity = record.repository.lower()
        else:
            parsed = urlparse(record.source)
            host = (parsed.hostname or "").lower()
            if host == "github.com":
                parts = [part for part in parsed.path.split("/") if part]
                if len(parts) >= 2:
                    canonical_identity = f"{parts[0]}/{parts[1]}".lower()
            if not canonical_identity:
                canonical_identity = host

        for token in unique_query:
            if len(token) < 5:
                continue
            if token in canonical_identity:
                df = self._document_frequency.get(token, 0)
                idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
                score += 2.25 * idf

        return score

    def retrieve(self, query: str, *, limit: int = 4) -> list[RetrievedChunk]:
        if limit <= 0:
            return []

        query_tokens = _tokens(query)
        ranked: list[tuple[float, KnowledgeRecord]] = []

        for record, counts, title_counts, document_length in zip(
            self._records,
            self._document_term_counts,
            self._title_term_counts,
            self._document_lengths,
        ):
            score = self._score(
                query_tokens,
                counts,
                title_counts,
                document_length,
                record,
            )
            if score > self.min_score:
                ranked.append((score, record))

        ranked.sort(key=lambda item: (-item[0], item[1].source, item[1].text))

        return [
            RetrievedChunk(
                text=record.text,
                source=record.source,
                score=round(score, 6),
                citation=f"S{index}",
            )
            for index, (score, record) in enumerate(ranked[:limit], start=1)
        ]
