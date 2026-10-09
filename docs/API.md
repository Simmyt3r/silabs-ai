# Silabs AI API

Development base URL: `http://127.0.0.1:8000`

## GET /v1/health

Returns service status without loading the model.

```json
{"status":"ok","app":"Silabs AI","version":"0.1.0","model_loaded":false}
```

## GET /v1/model

Returns configured model ID, adapter path, load state, device and dtype. This endpoint does not force a model download.

## POST /v1/chat

High-level conversational endpoint.

```json
{
  "message": "Explain recursion simply.",
  "history": [],
  "temperature": 0.7,
  "max_new_tokens": 256
}
```

Response:

```json
{
  "text": "...",
  "model": "HuggingFaceTB/SmolLM2-360M-Instruct",
  "finish_reason": "stop",
  "input_tokens": 24,
  "output_tokens": 80
}
```

## POST /v1/generate

Lower-level endpoint that accepts a complete role/content message array.

## Error behavior

Input validation errors use the standard FastAPI 422 response. Inference failures currently return 500. Before public production deployment, runtime failures should use stable public error codes while detailed exception information remains in server logs.

## Planned API hardening

- token streaming;
- authentication/API keys;
- request IDs;
- quotas and rate limits;
- product identity;
- structured retrieval citations;
- model routing;
- privacy-conscious usage telemetry.


## Guardrail completions

Both `POST /v1/chat` and `POST /v1/generate` apply the configured runtime
guardrail layer before model loading. When a request is intercepted, the normal
response schema is preserved with:

```json
{
  "finish_reason": "guardrail",
  "guardrail_category": "malicious_cyber",
  "input_tokens": 0,
  "output_tokens": 0
}
```

The text field contains the safe redirect/refusal. Model-status responses expose
`guardrails_enabled` so product clients can verify the runtime safety mode.

Guardrails can be disabled for controlled research with
`SILABS_ENABLE_GUARDRAILS=false`, but production deployments should keep them
enabled.
