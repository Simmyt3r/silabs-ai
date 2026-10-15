FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/tmp/huggingface \
    TRANSFORMERS_CACHE=/tmp/huggingface/transformers \
    SILABS_MODEL_PATH="" \
    SILABS_ALLOW_REMOTE_MODEL_DOWNLOAD=true \
    SILABS_DEVICE=cpu \
    SILABS_PRELOAD_MODEL=false \
    SILABS_API_HOST=0.0.0.0 \
    SILABS_API_PORT=7860

WORKDIR /app

COPY requirements.txt pyproject.toml ./
COPY api ./api
COPY silabs_ai ./silabs_ai
COPY scripts ./scripts
COPY clients ./clients
COPY knowledge ./knowledge
COPY models/registry.json ./models/registry.json

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
