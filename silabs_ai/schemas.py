from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant"]


class Message(BaseModel):
    role: Role
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[Message] = Field(default_factory=list)
    system_prompt: str | None = None
    max_new_tokens: int | None = Field(default=None, ge=1, le=4096)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, gt=0.0, le=1.0)


class GenerateRequest(BaseModel):
    messages: list[Message] = Field(min_length=1)
    max_new_tokens: int | None = Field(default=None, ge=1, le=4096)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, gt=0.0, le=1.0)


class GenerationResponse(BaseModel):
    text: str
    model: str
    finish_reason: str = "stop"
    guardrail_category: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    model_loaded: bool


class ModelStatusResponse(BaseModel):
    model_id: str
    adapter_path: str | None
    loaded: bool
    device: str
    dtype: str
    guardrails_enabled: bool
