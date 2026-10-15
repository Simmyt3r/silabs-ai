# Hugging Face Gradio Staging Deployment — Baby Steps

This is the fallback staging path for Silabs AI when Docker Space creation is not available.

The goal is simple:

**Put Silabs AI online in a Gradio Space, prove the model can answer, then connect UniXpress later.**

The Docker files remain in the repository for future deployment options. The active Hugging Face Space configuration now uses Gradio.

## Step 1 — Create the Space

On Hugging Face, create a new Space with:

- **Owner:** `silabtechnologies`
- **Space name:** `silabs-ai-staging`
- **SDK:** Gradio
- **Hardware:** Free tier / CPU Basic
- **License:** Apache-2.0
- **Visibility:** Private if available to you; otherwise Public for staging

If your account allows creation with those settings, continue.

## Step 2 — Do not attach a bucket yet

For the first deployment, leave the storage bucket out.

We first want to prove:

1. the Space builds;
2. Qwen3-1.7B loads;
3. authentication works;
4. one response can be generated.

The 47,493-record RAG corpus comes after that.

## Step 3 — Pull the latest repository in Colab

```bash
%cd /content/silabs-ai
!git pull origin main
```

The repository should now contain:

```text
app.py
README.md
requirements.txt
silabs_ai/
```

The top of `README.md` now tells Hugging Face to run:

```text
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
```

## Step 4 — Create a Hugging Face write token

In Hugging Face:

**Settings → Access Tokens → Create new token**

Give it write access to your Space.

Copy the token.

Never commit the token to GitHub.

## Step 5 — Login from Colab

```bash
!pip install -U huggingface_hub -q
!hf auth login
```

Paste the token.

## Step 6 — Add the Space as a Git remote

```bash
%cd /content/silabs-ai
!git remote remove hf 2>/dev/null || true
!git remote add hf https://huggingface.co/spaces/silabtechnologies/silabs-ai-staging
!git remote -v
```

You should see:

- `origin` → GitHub
- `hf` → Hugging Face Space

## Step 7 — Push the repository to Hugging Face

```bash
!git push hf main
```

Then open the Space page and watch the build logs.

## Step 8 — Add Space variables

Open:

**Space → Settings → Variables and secrets**

Add these Variables:

```text
SILABS_MODEL_PATH=
SILABS_ALLOW_REMOTE_MODEL_DOWNLOAD=true
SILABS_DEVICE=cpu
SILABS_DTYPE=float32
SILABS_PRELOAD_MODEL=false
SILABS_RAG_ENABLED=false
SILABS_API_AUTH_ENABLED=true
```

For the first staging deployment, RAG stays disabled.

## Step 9 — Add the API-key hash as a Secret

Add:

```text
SILABS_API_KEY_HASHES={"unixpress":"YOUR_UNIXPRESS_KEY_HASH"}
```

Use the **hash**, not the raw API key.

The raw key stays with the UniXpress/server-side client.

## Step 10 — Wait for the Space to become Running

When the Space finishes building, you should see the Silabs AI staging page.

It contains:

- Client ID
- API Key
- Message box
- Answer
- Sources
- Status

The default Client ID is:

```text
unixpress
```

## Step 11 — Test authentication

First enter:

- Client ID: `unixpress`
- Wrong API key
- Any message

It should reject the request.

Then use the real raw UniXpress key.

That should be accepted.

## Step 12 — Test the model

Use a short message:

```text
Explain what a database is in one short paragraph.
```

The first request may take a long time because:

1. Qwen3-1.7B has to download;
2. the weights have to load into memory;
3. CPU generation is slow.

That is acceptable for staging.

## Step 13 — What success looks like

Staging deployment is successful when:

- the Space builds;
- the page opens;
- bad credentials are rejected;
- correct credentials work;
- Qwen3-1.7B generates an answer;
- the response streams into the interface;
- status shows token counts;
- no model crash occurs.

## Step 14 — Do not connect UniXpress yet

After the basic Space works, the next deployment task is:

**Add the verified RAG corpus to a deployment-accessible Hugging Face dataset/storage location.**

Only after RAG is confirmed should UniXpress use the staging Space.

## Important note about the Gradio Space

This Gradio Space is a **staging deployment**, not the final production API.

It reuses the same Silabs AI engine, authentication, guardrails, rate limiting, telemetry, streaming, and citation logic, but Gradio is the front door instead of our FastAPI endpoints.

That is enough to prove remote model deployment before production hosting is chosen.
