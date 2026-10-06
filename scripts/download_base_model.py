from __future__ import annotations

from huggingface_hub import snapshot_download

from silabs_ai.config import get_settings


def main() -> None:
    settings = get_settings()
    path = snapshot_download(
        repo_id=settings.model_id,
        revision=settings.model_revision,
        cache_dir=settings.model_cache,
        allow_patterns=[
            "*.json",
            "*.model",
            "*.safetensors",
            "tokenizer*",
            "special_tokens_map.json",
            "generation_config.json",
        ],
    )
    print(f"Model available at: {path}")


if __name__ == "__main__":
    main()
