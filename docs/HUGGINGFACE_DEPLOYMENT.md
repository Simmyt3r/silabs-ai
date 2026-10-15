# Hugging Face Staging Deployment — Baby Steps

This guide deploys the current Silabs AI FastAPI service to a Hugging Face Docker Space.

The first goal is simple:

**Get the Silabs AI API online and confirm that it can answer one request.**

Do not enable the large RAG knowledge corpus during the first deployment. Add it after the basic API is confirmed working.

## Before you start

You need:

1. A Hugging Face account.
2. Access to create a Docker Space.
3. A Hugging Face write token.
4. The raw UniXpress Silabs AI API key that was generated earlier.
5. The matching SHA-256 hash for that key.

Current Hugging Face policy may require a paid account tier to create a new Docker/Gradio compute Space even though CPU Basic has no hourly hardware charge. If Docker Space creation is blocked on your account, do not change the Silabs AI code. The deployment target is the only thing that needs to change.

---

## Step 1 — Pull the latest Silabs AI code

In Colab:

```bash
%cd /content/silabs-ai
!git pull origin main
```

You should now have:

- `Dockerfile`
- `.dockerignore`
- Hugging Face metadata at the top of `README.md`

---

## Step 2 — Create the Hugging Face Space

Go to Hugging Face and create a new Space.

Use:

- **Space name:** `silabs-ai-staging`
- **SDK:** Docker
- **Hardware:** CPU Basic
- **Visibility:** private if your account allows it; otherwise use the visibility you are comfortable testing with

Do not add application code manually in the browser.

The Space is only the destination for the repository.

---

## Step 3 — Create a Hugging Face write token

In Hugging Face account settings:

1. Open **Access Tokens**.
2. Create a token with permission to write to the new Space.
3. Copy the token.

Do not commit this token to GitHub.

---

## Step 4 — Log in from Colab

Install/update the Hub CLI if needed:

```bash
!pip install -U huggingface_hub -q
```

Then:

```bash
!hf auth login
```

Paste the Hugging Face token when prompted.

If asked whether to save it as a Git credential, choose **yes**.

---

## Step 5 — Add the Hugging Face Space as a Git remote

Replace `YOUR_HF_USERNAME` with your Hugging Face username:

```bash
%cd /content/silabs-ai
!git remote remove hf 2>/dev/null || true
!git remote add hf https://huggingface.co/spaces/YOUR_HF_USERNAME/silabs-ai-staging
```

Check:

```bash
!git remote -v
```

You should see both:

- `origin` pointing to GitHub
- `hf` pointing to the Hugging Face Space

---

## Step 6 — Push Silabs AI to the Space

Run:

```bash
!git push hf main
```

Hugging Face will begin building the Docker image automatically.

Open the Space page and watch **Logs**.

The first build can take several minutes because Python packages must be installed.

---

## Step 7 — Add the Silabs AI server settings

Open:

**Space → Settings → Variables and secrets**

For the first staging deployment add:

### Variable

```text
SILABS_API_AUTH_ENABLED=true
```

### Secret

Use the API-key hash generated earlier:

```text
SILABS_API_KEY_HASHES={"unixpress":"YOUR_API_KEY_HASH"}
```

For the first deployment leave RAG disabled:

```text
SILABS_RAG_ENABLED=false
```

The Docker image already tells Silabs AI to:

- download `Qwen/Qwen3-1.7B` from Hugging Face when needed;
- run on CPU;
- listen on port `7860`;
- avoid loading the model until the first generation request.

Never place the raw UniXpress API key in the Space server settings. The server stores only its hash.

---

## Step 8 — Wait until the Space says Running

When deployment succeeds, the Space URL will look similar to:

```text
https://YOUR_HF_USERNAME-silabs-ai-staging.hf.space
```

Open that URL.

Expected response:

```json
{
  "name": "Silabs AI",
  "status": "running",
  "docs": "/docs",
  "health": "/v1/health",
  "ready": "/v1/ready"
}
```

Also test:

```text
https://YOUR_HF_USERNAME-silabs-ai-staging.hf.space/v1/health
```

and:

```text
https://YOUR_HF_USERNAME-silabs-ai-staging.hf.space/docs
```

If these work, the API container is online.

---

## Step 9 — Test one real AI request from Colab

Use the **raw** UniXpress key here. Do not use the hash.

```python
import requests

SPACE_URL = "https://YOUR_HF_USERNAME-silabs-ai-staging.hf.space"
RAW_API_KEY = "YOUR_RAW_UNIXPRESS_KEY"

response = requests.post(
    f"{SPACE_URL}/v1/chat",
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

print("status:", response.status_code)
print(response.text)
```

The first request is the slowest because the model must download and load.

CPU Basic will also generate slowly. This deployment is for **staging and integration testing**, not final production performance.

A successful response means:

**GitHub code → Hugging Face Silabs AI server → authenticated API response**

is working.

---

## Step 10 — Only then add the knowledge corpus

Do not enable RAG until the base staging API passes Step 9.

The verified corpus currently lives outside Git in:

```text
verified-expanded.jsonl
```

It contains 47,493 verified chunks.

The next deployment task is to place that corpus in an appropriate Hugging Face-hosted data location or other deployment-accessible storage, then configure:

```text
SILABS_RAG_ENABLED=true
SILABS_KNOWLEDGE_PATH=<deployed corpus path>
```

Do not upload the corpus blindly into the GitHub repository just to make deployment easier.

---

## What counts as successful staging deployment?

Do not connect UniXpress yet unless all of these pass:

- Space status is **Running**.
- `/` works.
- `/v1/health` returns HTTP 200.
- `/docs` loads.
- Missing API credentials return HTTP 401.
- Correct UniXpress credentials return HTTP 200.
- A real model response is generated.
- Request IDs appear.
- `/v1/usage` works for the UniXpress client.

After these checks, staging deployment is complete and UniXpress integration can begin against a real URL.
