from silabs_ai.telemetry import InMemoryUsageTracker


def test_usage_tracker_records_per_client_metrics():
    tracker = InMemoryUsageTracker()

    tracker.record(
        client_id="unixpress",
        input_tokens=10,
        output_tokens=5,
        rag_used=True,
        citation_repaired=True,
        latency_ms=125.5,
    )
    tracker.record(
        client_id="unixpress",
        input_tokens=4,
        output_tokens=2,
        guardrail_intercepted=True,
        latency_ms=74.5,
    )

    usage = tracker.snapshot("unixpress")["unixpress"]

    assert usage["requests"] == 2
    assert usage["input_tokens"] == 14
    assert usage["output_tokens"] == 7
    assert usage["rag_requests"] == 1
    assert usage["citation_repairs"] == 1
    assert usage["guardrail_intercepts"] == 1
    assert usage["failures"] == 0
    assert usage["total_latency_ms"] == 200.0
    assert usage["average_latency_ms"] == 100.0


def test_usage_tracker_isolates_clients():
    tracker = InMemoryUsageTracker()
    tracker.record(client_id="unixpress", input_tokens=3)
    tracker.record(client_id="chombutar", input_tokens=9)

    assert tracker.snapshot("unixpress")["unixpress"]["input_tokens"] == 3
    assert tracker.snapshot("chombutar")["chombutar"]["input_tokens"] == 9
