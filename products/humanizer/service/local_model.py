"""Offline-only generation adapters. No remote URL, auth or HTTP access."""
from __future__ import annotations

from pathlib import Path


class GGUFLocalModel:
    """CPU/GPU local inference through llama-cpp-python.

    Install llama-cpp-python separately. A valid local GGUF model is required.
    The model is never downloaded implicitly.
    """

    def __init__(
        self,
        model_path: str | Path,
        *,
        context_tokens: int = 4096,
        max_new_tokens: int = 384,
        threads: int | None = None,
        gpu_layers: int = 0,
    ) -> None:
        path = Path(model_path).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() != ".gguf":
            raise FileNotFoundError(f"Local .gguf file required: {path}")
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "Install a compatible local llama-cpp-python build to use the GGUF backend."
            ) from exc

        kwargs = {"model_path": str(path), "n_ctx": context_tokens, "n_gpu_layers": gpu_layers, "verbose": False}
        if threads is not None:
            kwargs["n_threads"] = threads
        self.model = Llama(**kwargs)
        self.max_new_tokens = max_new_tokens

    def __call__(self, prompt: str) -> str:
        # /no_think is supported by Qwen3 and reduces reasoning-token waste
        # for short, bounded document transformations.
        reply = self.model.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a careful offline writing editor. Output only the revised text."},
                {"role": "user", "content": prompt + "\n/no_think"},
            ],
            max_tokens=self.max_new_tokens,
            temperature=0.25,
            top_p=0.9,
            repeat_penalty=1.08,
        )
        content = reply["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise RuntimeError("Local model returned no text.")
        # A rare Qwen3 template may emit a closed thinking block.
        if "</think>" in content:
            content = content.split("</think>", 1)[1]
        return content.strip()


class TransformersLocalModel:
    """Use the existing Silabs AI engine with an already downloaded HF model."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        max_new_tokens: int = 384,
        device: str = "cpu",
        dtype: str = "float32",
    ) -> None:
        path = Path(model_path).expanduser().resolve()
        if not path.is_dir() or not (path / "config.json").is_file():
            raise FileNotFoundError(f"Downloaded local Transformers model required: {path}")

        from silabs_ai.config import Settings
        from silabs_ai.engine import SilabsAIEngine

        settings = Settings(
            _env_file=None,
            model_path=str(path),
            model_cache=None,
            allow_remote_model_download=False,
            adapter_path=None,
            device=device,
            dtype=dtype,
            rag_enabled=False,
            knowledge_path=None,
            enable_thinking=False,
        )
        self.engine = SilabsAIEngine(settings=settings)
        self.max_new_tokens = max_new_tokens

    def __call__(self, prompt: str) -> str:
        result = self.engine.generate(
            [{"role": "user", "content": prompt}],
            max_new_tokens=self.max_new_tokens,
            temperature=0.25,
        )
        return result.text.strip()
