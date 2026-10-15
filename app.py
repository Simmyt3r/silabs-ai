from __future__ import annotations

import time

import spaces
import gradio as gr

from silabs_ai.auth import authenticate_api_key
from silabs_ai.config import get_settings
from silabs_ai.engine import SilabsAIEngine
from silabs_ai.rate_limit import InMemoryRateLimiter, enforce_rate_limit
from silabs_ai.telemetry import InMemoryUsageTracker


settings = get_settings()
engine = SilabsAIEngine(settings)
rate_limiter = InMemoryRateLimiter()
usage_tracker = InMemoryUsageTracker()


def _source_rows(result) -> list[list[str]]:
    rows = []
    for item in result.sources:
        if not item.source:
            continue
        rows.append([
            item.citation or "",
            item.source,
            "" if item.score is None else str(item.score),
        ])
    return rows


@spaces.GPU(duration=120)
def ask_silabs(
    message: str,
    client_id: str,
    api_key: str,
):
    message = (message or "").strip()
    client_id = (client_id or "").strip()
    api_key = (api_key or "").strip()

    if not message:
        raise gr.Error("Enter a message first.")

    try:
        principal = authenticate_api_key(
            x_silabs_api_key=api_key or None,
            x_silabs_client=client_id or None,
            settings=settings,
        )
    except Exception as exc:
        raise gr.Error("Invalid Silabs AI credentials.") from exc

    client_limits = settings.rate_limit_overrides.get(principal.client_id, {})
    try:
        enforce_rate_limit(
            rate_limiter,
            client_id=principal.client_id,
            route="chat",
            limit=client_limits.get("chat", settings.rate_limit_chat_per_minute),
        )
    except Exception as exc:
        raise gr.Error("Rate limit exceeded. Try again shortly.") from exc

    started = time.perf_counter()
    streamed_text = ""
    final_result = None

    try:
        for event in engine.stream_chat(
            message,
            max_new_tokens=192,
            temperature=0.0,
        ):
            if event["type"] == "chunk":
                streamed_text += event["text"]
                yield (
                    streamed_text,
                    [],
                    "Generating...",
                )
            elif event["type"] == "final":
                final_result = event["result"]
    except Exception as exc:
        usage_tracker.record(
            client_id=principal.client_id,
            failed=True,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        raise gr.Error(f"Generation failed: {exc}") from exc

    if final_result is None:
        raise gr.Error("Generation ended without a final answer.")

    usage_tracker.record(
        client_id=principal.client_id,
        input_tokens=final_result.input_tokens,
        output_tokens=final_result.output_tokens,
        rag_used=bool(final_result.sources),
        guardrail_intercepted=final_result.finish_reason == "guardrail",
        citation_repaired=final_result.citation_repaired,
        latency_ms=(time.perf_counter() - started) * 1000,
    )

    yield (
        final_result.text,
        _source_rows(final_result),
        (
            f"Done · input tokens: {final_result.input_tokens} · "
            f"output tokens: {final_result.output_tokens} · "
            f"citation repaired: {final_result.citation_repaired}"
        ),
    )


with gr.Blocks(title="Silabs AI Staging") as demo:
    gr.Markdown(
        """
# Silabs AI — Staging

This Space is for deployment and integration testing.

The first request can be slow because the model may need to download and load.
"""
    )

    with gr.Row():
        client_id = gr.Textbox(
            label="Client ID",
            value="unixpress",
        )
        api_key = gr.Textbox(
            label="API Key",
            type="password",
            placeholder="Paste the raw UniXpress key",
        )

    message = gr.Textbox(
        label="Message",
        placeholder="Ask Silabs AI something...",
        lines=4,
    )
    submit = gr.Button("Ask Silabs AI", variant="primary")

    answer = gr.Markdown(label="Answer")
    sources = gr.Dataframe(
        headers=["Citation", "Source", "Score"],
        datatype=["str", "str", "str"],
        label="Sources",
        interactive=False,
    )
    status = gr.Textbox(label="Status", interactive=False)

    submit.click(
        fn=ask_silabs,
        inputs=[message, client_id, api_key],
        outputs=[answer, sources, status],
        api_name="chat",
    )

    message.submit(
        fn=ask_silabs,
        inputs=[message, client_id, api_key],
        outputs=[answer, sources, status],
        api_name=False,
    )


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch()
