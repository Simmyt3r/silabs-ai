from __future__ import annotations

from pathlib import Path

from huggingface_hub import snapshot_download

from silabs_ai.config import get_settings


def main() -> None:
    settings = get_settings()
    if not settings.model_path:
        raise RuntimeError("SILABS_MODEL_PATH must be set for repo-local model loading.")

    target = Path(settings.model_path).expanduser()
    target.mkdir(parents=True, exist_ok=True)

    path = snapshot_download(
        repo_id=settings.model_id,
        revision=settings.model_revision,
        local_dir=str(target),
        allow_patterns=[
            "*.json",
            "*.model",
            "*.safetensors",
            "tokenizer*",
            "special_tokens_map.json",
            "generation_config.json",
        ],
    )

    print(f"Silabs AI base model downloaded to: {path}")
    print("Verify with: python -m scripts.verify_model --load-weights")


if __name__ == "__main__":
    main()
