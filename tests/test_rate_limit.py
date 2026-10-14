from fastapi import HTTPException

from silabs_ai.rate_limit import InMemoryRateLimiter, enforce_rate_limit


def test_rate_limiter_allows_within_limit():
    limiter = InMemoryRateLimiter(window_seconds=60)

    first = limiter.check(client_id="unixpress", route="chat", limit=2, now=100)
    second = limiter.check(client_id="unixpress", route="chat", limit=2, now=101)

    assert first.allowed is True
    assert first.remaining == 1
    assert second.allowed is True
    assert second.remaining == 0


def test_rate_limiter_rejects_after_limit():
    limiter = InMemoryRateLimiter(window_seconds=60)

    limiter.check(client_id="unixpress", route="chat", limit=1, now=100)
    decision = limiter.check(client_id="unixpress", route="chat", limit=1, now=101)

    assert decision.allowed is False
    assert decision.retry_after > 0


def test_rate_limiter_isolated_by_client_and_route():
    limiter = InMemoryRateLimiter(window_seconds=60)

    limiter.check(client_id="unixpress", route="chat", limit=1, now=100)

    other_client = limiter.check(
        client_id="chombutar", route="chat", limit=1, now=101
    )
    other_route = limiter.check(
        client_id="unixpress", route="generate", limit=1, now=101
    )

    assert other_client.allowed is True
    assert other_route.allowed is True


def test_rate_limiter_resets_next_window():
    limiter = InMemoryRateLimiter(window_seconds=60)

    limiter.check(client_id="unixpress", route="chat", limit=1, now=59)
    blocked = limiter.check(client_id="unixpress", route="chat", limit=1, now=59)
    reset = limiter.check(client_id="unixpress", route="chat", limit=1, now=60)

    assert blocked.allowed is False
    assert reset.allowed is True


def test_enforce_rate_limit_raises_429():
    limiter = InMemoryRateLimiter(window_seconds=60)
    limiter.check(client_id="unixpress", route="chat", limit=1, now=100)

    # Freeze time by filling the actual current bucket for this assertion.
    live = InMemoryRateLimiter(window_seconds=60)
    enforce_rate_limit(live, client_id="unixpress", route="chat", limit=1)

    try:
        enforce_rate_limit(live, client_id="unixpress", route="chat", limit=1)
    except HTTPException as exc:
        assert exc.status_code == 429
        assert "Retry-After" in exc.headers
    else:
        raise AssertionError("Expected a 429 rate-limit response")
