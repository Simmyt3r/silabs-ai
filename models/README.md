# Local models

Silabs AI keeps model metadata in Git and model weights on the machine that runs training or inference.

The v1 base model is materialized at:

```text
models/base/SmolLM2-360M-Instruct/
```

Download it with:

```bash
python -m scripts.download_base_model
```

Then verify the complete local load with:

```bash
python -m scripts.verify_model --load-weights
```

The inference engine always prefers this local directory. If it is missing and
`SILABS_ALLOW_REMOTE_MODEL_DOWNLOAD=true`, the engine can fall back to the
configured Hugging Face model ID.

Weight files are intentionally ignored by Git. Committing hundreds of megabytes
of generated model artifacts to normal Git history would make the repository
slower, harder to clone, and harder to maintain. Model identity and provenance
live in `models/registry.json`.
