from __future__ import annotations

from functools import lru_cache
from typing import Literal

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
    model_id: str = "HuggingFaceTB/SmolLM2-360M-Instruct"
    model_revision: str = "main"
    model_cache: str | None = None
    adapter_path: str | None = None
    device: str = "auto"
    dtype: Literal["auto", "float32", "float16", "bfloat16"] = "auto"
    trust_remote_code: bool = False
    preload_model: bool = False

    system_prompt: str = (
        "You are Silabs AI, a helpful, clear and careful assistant built by "
        "Simeon's Laboratories and Co Technologies Ltd."
    )
    max_new_tokens: int = 384
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.08

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
