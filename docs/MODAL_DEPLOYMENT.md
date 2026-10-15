# Modal Staging Deployment — Baby Steps

This is the current staging deployment path for Silabs AI.

Modal can expose the existing FastAPI application directly, so the deployed service keeps the real Silabs AI endpoints instead of using a separate demo interface.

## What will be deployed

The staging flow is:

GitHub repository → Modal T4 container → Silabs AI FastAPI → UniXpress later

The first deployment keeps RAG disabled. The verified knowledge corpus is added after the base remote API works.

## Step 1 — Create a Modal account

Open Modal and create/sign in to your account.

For staging, stay on the Starter/free-credit plan unless Modal explicitly requires otherwise.

## Step 2 — Start a fresh Colab runtime

Run:

```bash
%cd /content
!rm -rf silabs-ai
!git clone https://github.com/Simmyt3r/silabs-ai.git
%cd /content/silabs-ai
```

## Step 3 — Install Modal CLI

```bash
!pip install -U modal -q
```

## Step 4 — Authenticate Colab with Modal

Run:

```bash
!modal setup
```

Modal will print a browser link.

Open the link, approve the authentication, then return to Colab.

## Step 5 — Create the Silabs AI Modal secret

First generate a fresh UniXpress API key if the previous raw key/hash pair was lost:

```bash
!python -m scripts.generate_api_key unixpress
```

Save the raw key somewhere private.

Copy the SHA-256 hash.

Then create the Modal secret:

```bash
!modal secret create silabs-ai-secrets \
  SILABS_MODEL_PATH="" \
  SILABS_MODEL_ID="Qwen/Qwen3-1.7B" \
  SILABS_ALLOW_REMOTE_MODEL_DOWNLOAD="true" \
  SILABS_DEVICE="cuda" \
  SILABS_DTYPE="float16" \
  SILABS_PRELOAD_MODEL="false" \
  SILABS_RAG_ENABLED="false" \
  SILABS_API_AUTH_ENABLED="true" \
  SILABS_API_KEY_HASHES='{"unixpress":"YOUR_UNIXPRESS_KEY_HASH"}'
```

Replace only `YOUR_UNIXPRESS_KEY_HASH`.

Do not put the raw API key in this secret. The server needs only the hash.

## Step 6 — Prepare the persistent model cache

Download Qwen once into the Modal Volume:

```bash
!modal run modal_app.py::prepare_model_cache
```

Wait for it to finish.

This stores the model in the persistent `silabs-ai-model-cache` Volume so later containers can reuse it.

## Step 7 — Test the Modal definition

```bash
!modal serve modal_app.py
```

Modal builds the image and prints a temporary development URL.

Keep this cell running while testing.

## Step 8 — Test health

Open a second Colab cell and replace `YOUR_MODAL_DEV_URL`:

```python
import requests

BASE_URL = "YOUR_MODAL_DEV_URL".rstrip("/")

r = requests.get(f"{BASE_URL}/v1/health", timeout=60)
print(r.status_code)
print(r.text)
```

Expected HTTP status:

```text
200
```

## Step 9 — Test authentication

With no credentials:

```python
r = requests.post(
    f"{BASE_URL}/v1/chat",
    json={"message": "Hello"},
    timeout=60,
)
print(r.status_code)
print(r.text)
```

Expected:

```text
401
```

## Step 10 — Test one real model response

Use the raw API key, not the hash:

```python
RAW_API_KEY = "YOUR_RAW_UNIXPRESS_KEY"

r = requests.post(
    f"{BASE_URL}/v1/chat",
    headers={
        "X-Silabs-Client": "unixpress",
        "X-Silabs-API-Key": RAW_API_KEY,
    },
    json={
        "message": "Explain what a database is in one short paragraph.",
        "temperature": 0,
        "max_new_tokens": 80,
    },
    timeout=1200,
)

print(r.status_code)
print(r.text)
```

The first model request can be slow because Qwen3-1.7B must download into the persistent Modal model-cache volume and load on the T4.

Later cold starts can reuse the cached model files.

## Step 11 — Deploy the permanent staging URL

Stop `modal serve` after the development test passes.

Then run:

```bash
!modal deploy modal_app.py
```

Modal prints the deployed application URL.

That URL becomes:

```text
SILABS_AI_URL=<your Modal URL>
```

for future UniXpress staging integration.

## Step 12 — Verify the deployed staging API

Check:

- `GET /v1/health` → 200
- request without credentials → 401
- correct UniXpress credentials → 200
- `GET /v1/usage` works
- `POST /v1/chat/stream` streams SSE events
- request IDs are returned

Only after these pass should the staging-deployment roadmap item be marked complete.

## Step 13 — RAG comes next

The initial Modal deployment intentionally uses:

```text
SILABS_RAG_ENABLED=false
```

After the base API is stable, deploy the verified 47,493-record corpus to persistent storage and enable RAG.

Do not copy the corpus into GitHub merely for deployment convenience.
