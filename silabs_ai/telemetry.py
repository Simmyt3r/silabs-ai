from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import asdict, dataclass


@dataclass
class UsageStats:
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    rag_requests: int = 0
    guardrail_intercepts: int = 0
    citation_repairs: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        if self.requests <= 0:
            return 0.0
        return self.total_latency_ms / self.requests

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["average_latency_ms"] = round(self.average_latency_ms, 2)
        payload["total_latency_ms"] = round(self.total_latency_ms, 2)
        return payload


class InMemoryUsageTracker:
    """Thread-safe per-client usage accounting for one API process."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stats: dict[str, UsageStats] = defaultdict(UsageStats)

    def record(
        self,
        *,
        client_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        rag_used: bool = False,
        guardrail_intercepted: bool = False,
        citation_repaired: bool = False,
        failed: bool = False,
        latency_ms: float = 0.0,
    ) -> None:
        with self._lock:
            stats = self._stats[client_id]
            stats.requests += 1
            stats.input_tokens += max(input_tokens, 0)
            stats.output_tokens += max(output_tokens, 0)
            stats.rag_requests += int(rag_used)
            stats.guardrail_intercepts += int(guardrail_intercepted)
            stats.citation_repairs += int(citation_repaired)
            stats.failures += int(failed)
            stats.total_latency_ms += max(latency_ms, 0.0)

    def snapshot(self, client_id: str | None = None) -> dict:
        with self._lock:
            if client_id is not None:
                return {client_id: self._stats[client_id].to_dict()}
            return {
                key: value.to_dict()
                for key, value in sorted(self._stats.items())
            }
