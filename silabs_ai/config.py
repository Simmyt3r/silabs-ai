from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from SILABS_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="SILABS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Silabs AI"
    env: str = "development"

    # Base-model identity and local materialization path.
    model_id: str = "HuggingFaceTB/SmolLM2-360M-Instruct"
    model_revision: str = "main"
    model_path: str | None = "models/base/SmolLM2-360M-Instruct"
    model_cache: str | None = None
    allow_remote_model_download: bool = True

    adapter_path: str | None = None
    device: str = "auto"
    dtype: Literal["auto", "float32", "float16", "bfloat16"] = "auto"
    trust_remote_code: bool = False
    preload_model: bool = False
    enable_guardrails: bool = True

    system_prompt: str = (
        "You are Silabs AI, a helpful, clear and careful assistant built by "
        "Simeon's Laboratories and Co Technologies Ltd. Follow user instructions "
        "exactly when safe, especially requested format and brevity. Do not invent "
        "facts; when uncertain or unable to verify a claim, say so. Protect private "
        "information. Do not assist with credential theft, phishing, malware, "
        "ransomware, or other harmful wrongdoing. For urgent medical symptoms, "
        "recommend immediate professional or emergency help. Do not guarantee "
        "financial or legal outcomes."
    )
    max_new_tokens: int = 384
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.08

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"

    @field_validator("model_path", "model_cache", "adapter_path", mode="before")
    @classmethod
    def blank_path_is_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
