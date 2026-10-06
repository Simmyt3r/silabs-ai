from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from silabs_ai import __version__
from silabs_ai.config import get_settings
from silabs_ai.engine import SilabsAIEngine
from silabs_ai.schemas import ChatRequest, GenerateRequest, GenerationResponse, HealthResponse, ModelStatusResponse

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
    )


@app.post("/v1/chat", response_model=GenerationResponse)
def chat(payload: ChatRequest) -> GenerationResponse:
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
        logging.getLogger(__name__).exception("Chat generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerationResponse(
        text=result.text,
        model=settings.model_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )


@app.post("/v1/generate", response_model=GenerationResponse)
def generate(payload: GenerateRequest) -> GenerationResponse:
    try:
        result = engine.generate(
            [message.model_dump() for message in payload.messages],
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
        )
    except Exception as exc:
        logging.getLogger(__name__).exception("Generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerationResponse(
        text=result.text,
        model=settings.model_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
