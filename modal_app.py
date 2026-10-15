from __future__ import annotations

import modal


APP_NAME = "silabs-ai-staging"
MODEL_CACHE = "/cache/huggingface"

app = modal.App(APP_NAME)

model_cache = modal.Volume.from_name(
    "silabs-ai-model-cache",
    create_if_missing=True,
)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.4",
        "transformers>=4.46,<5",
        "accelerate>=1.0,<2",
        "peft>=0.13,<1",
        "safetensors>=0.4",
        "sentencepiece>=0.2",
        "huggingface-hub>=0.26,<2",
        "fastapi>=0.115,<1",
        "uvicorn[standard]>=0.30,<1",
        "pydantic>=2.8,<3",
        "pydantic-settings>=2.5,<3",
    )
    .add_local_python_source("silabs_ai", "api")
)


@app.function(
    image=image,
    gpu="T4",
    timeout=1200,
    scaledown_window=300,
    volumes={MODEL_CACHE: model_cache},
    secrets=[modal.Secret.from_name("silabs-ai-secrets")],
)
@modal.asgi_app()
def fastapi_app():
    import os

    os.environ.setdefault("HF_HOME", MODEL_CACHE)
    os.environ.setdefault("HF_HUB_CACHE", f"{MODEL_CACHE}/hub")
    os.environ.setdefault("TRANSFORMERS_CACHE", f"{MODEL_CACHE}/transformers")

    from api.main import app as web_app

    return web_app
