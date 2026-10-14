from __future__ import annotations

import logging
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request

from silabs_ai import __version__
from silabs_ai.auth import APIPrincipal, require_api_key
from silabs_ai.config import get_settings
from silabs_ai.engine import SilabsAIEngine
from silabs_ai.rate_limit import InMemoryRateLimiter, enforce_rate_limit
from silabs_ai.schemas import ChatRequest, GenerateRequest, GenerationResponse, HealthResponse, ModelStatusResponse, UsageResponse
from silabs_ai.telemetry import InMemoryUsageTracker

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Silabs AI API",
    version=__version__,
    description="Shared inference API for Silabs AI.",
)
engine = SilabsAIEngine(settings)
rate_limiter = InMemoryRateLimiter()
usage_tracker = InMemoryUsageTracker()



@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.on_event("startup")
def startup() -> None:
    if settings.preload_model:
        engine.load()


@app.get("/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=__version__,
        model_loaded=engine.loaded,
    )


@app.get("/v1/model", response_model=ModelStatusResponse)
def model_status() -> ModelStatusResponse:
    return ModelStatusResponse(
        model_id=settings.model_id,
        adapter_path=settings.adapter_path,
        loaded=engine.loaded,
        device=settings.device,
        dtype=settings.dtype,
        guardrails_enabled=settings.enable_guardrails,
        rag_enabled=settings.rag_enabled,
        knowledge_path=settings.knowledge_path,
    )


@app.post("/v1/chat", response_model=GenerationResponse)
def chat(
    request: Request,
    payload: ChatRequest,
    principal: APIPrincipal = Depends(require_api_key),
) -> GenerationResponse:
    client_limits = settings.rate_limit_overrides.get(principal.client_id, {})
    enforce_rate_limit(
        rate_limiter,
        client_id=principal.client_id,
        route="chat",
        limit=client_limits.get("chat", settings.rate_limit_chat_per_minute),
    )
    started = time.perf_counter()
    request_id = request.state.request_id
    logging.getLogger(__name__).info(
        "chat request request_id=%s client=%s", request_id, principal.client_id
    )
    try:
        result = engine.chat(
            payload.message,
            payload.history,
            system_prompt=payload.system_prompt,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
        )
    except Exception as exc:
        usage_tracker.record(
            client_id=principal.client_id,
            failed=True,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        logging.getLogger(__name__).exception(
            "Chat generation failed request_id=%s client=%s",
            request_id,
            principal.client_id,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    usage_tracker.record(
        client_id=principal.client_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        rag_used=bool(result.sources),
        guardrail_intercepted=result.finish_reason == "guardrail",
        citation_repaired=result.citation_repaired,
        latency_ms=(time.perf_counter() - started) * 1000,
    )
    return GenerationResponse(
        request_id=request_id,
        text=result.text,
        model=settings.model_id,
        finish_reason=result.finish_reason,
        guardrail_category=result.guardrail_category,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        sources=[
            {"citation": item.citation, "source": item.source, "score": item.score}
            for item in result.sources
            if item.source
        ],
        citation_repaired=result.citation_repaired,
    )


@app.post("/v1/generate", response_model=GenerationResponse)
def generate(
    request: Request,
    payload: GenerateRequest,
    principal: APIPrincipal = Depends(require_api_key),
) -> GenerationResponse:
    client_limits = settings.rate_limit_overrides.get(principal.client_id, {})
    enforce_rate_limit(
        rate_limiter,
        client_id=principal.client_id,
        route="generate",
        limit=client_limits.get("generate", settings.rate_limit_generate_per_minute),
    )
    started = time.perf_counter()
    request_id = request.state.request_id
    logging.getLogger(__name__).info(
        "generate request request_id=%s client=%s", request_id, principal.client_id
    )
    try:
        result = engine.generate(
            [message.model_dump() for message in payload.messages],
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
        )
    except Exception as exc:
        usage_tracker.record(
            client_id=principal.client_id,
            failed=True,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        logging.getLogger(__name__).exception(
            "Generation failed request_id=%s client=%s",
            request_id,
            principal.client_id,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    usage_tracker.record(
        client_id=principal.client_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        guardrail_intercepted=result.finish_reason == "guardrail",
        citation_repaired=result.citation_repaired,
        latency_ms=(time.perf_counter() - started) * 1000,
    )
    return GenerationResponse(
        request_id=request_id,
        text=result.text,
        model=settings.model_id,
        finish_reason=result.finish_reason,
        guardrail_category=result.guardrail_category,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        sources=[
            {"citation": item.citation, "source": item.source, "score": item.score}
            for item in result.sources
            if item.source
        ],
        citation_repaired=result.citation_repaired,
    )


@app.get("/v1/usage", response_model=UsageResponse)
def usage(
    principal: APIPrincipal = Depends(require_api_key),
) -> UsageResponse:
    snapshot = usage_tracker.snapshot(principal.client_id)[principal.client_id]
    return UsageResponse(client_id=principal.client_id, usage=snapshot)
