"""Build-time download of a pinned, redistributable Qwen3 GGUF.

This script runs only on the GitHub Windows packaging runner. The installed
application never needs to contact Hugging Face.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO = "ggml-org/Qwen3-1.7B-GGUF"
FILENAME = "Qwen3-1.7B-Q4_K_M.gguf"
EXPECTED_SHA256 = "d2387ca2dbfee2ffabce7120d3770dadca0b293052bc2f0e138fdc940d9bc7b5"


def main() -> None:
    target_dir = Path("_ci_weights")
    target_dir.mkdir(parents=True, exist_ok=True)
    model = Path(
        hf_hub_download(
            repo_id=REPO,
            filename=FILENAME,
            local_dir=target_dir,
        )
    )
    with model.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Model SHA-256 mismatch: {digest}")
    if model.stat().st_size < 1_000_000_000:
        raise RuntimeError("GGUF model appears incomplete")
    with model.open("rb") as handle:
        if handle.read(4) != b"GGUF":
            raise RuntimeError("Model header is not GGUF")
    print(f"Verified official GGUF: {model} ({model.stat().st_size} bytes) SHA-256={digest}")


if __name__ == "__main__":
    main()
