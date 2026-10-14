from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


class InMemoryRateLimiter:
    """Simple per-client fixed-window limiter for a single API process.

    This is intentionally dependency-free for the first production hardening
    pass. Multi-instance deployment should replace it with a shared backend.
    """

    def __init__(self, *, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._buckets: dict[tuple[str, str], tuple[int, int]] = {}

    def check(
        self,
        *,
        client_id: str,
        route: str,
        limit: int,
        now: float | None = None,
    ) -> RateLimitDecision:
        if limit <= 0:
            return RateLimitDecision(True, 0, 0)

        current = int(time.time() if now is None else now)
        window_start = current - (current % self.window_seconds)
        key = (client_id, route)

        with self._lock:
            stored_window, count = self._buckets.get(key, (window_start, 0))
            if stored_window != window_start:
                stored_window, count = window_start, 0

            if count >= limit:
                retry_after = max(
                    1,
                    self.window_seconds - (current - window_start),
                )
                return RateLimitDecision(False, 0, retry_after)

            count += 1
            self._buckets[key] = (stored_window, count)

        return RateLimitDecision(
            allowed=True,
            remaining=max(limit - count, 0),
            retry_after=0,
        )


def enforce_rate_limit(
    limiter: InMemoryRateLimiter,
    *,
    client_id: str,
    route: str,
    limit: int,
) -> RateLimitDecision:
    decision = limiter.check(
        client_id=client_id,
        route=route,
        limit=limit,
    )
    if decision.allowed:
        return decision

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Silabs AI rate limit exceeded.",
        headers={"Retry-After": str(decision.retry_after)},
    )
