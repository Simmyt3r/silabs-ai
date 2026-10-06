from __future__ import annotations

import argparse

from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

from silabs_ai.config import get_settings
from silabs_ai.model_source import resolve_model_source


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the Silabs AI base model")
    parser.add_argument(
        "--load-weights",
        action="store_true",
        help="Load the full model weights and report parameter count.",
    )
    args = parser.parse_args()

    settings = get_settings()
    source = resolve_model_source(
        local_path=settings.model_path,
        remote_id=settings.model_id,
        allow_remote=False,
    )

    config = AutoConfig.from_pretrained(source.value, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(source.value, local_files_only=True)

    print(f"Model source: {source.value}")
    print(f"Architecture: {getattr(config, 'model_type', 'unknown')}")
    print(f"Tokenizer vocabulary: {len(tokenizer):,}")

    if args.load_weights:
        model = AutoModelForCausalLM.from_pretrained(
            source.value,
            local_files_only=True,
            torch_dtype="auto",
        )
        parameters = sum(parameter.numel() for parameter in model.parameters())
        print(f"Loaded weights successfully: {parameters:,} parameters")

    print("Silabs AI base model verification: PASS")


if __name__ == "__main__":
    main()
