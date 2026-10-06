from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelSource:
    """Resolved model location used by inference and training."""

    value: str
    is_local: bool


def local_model_ready(path: str | Path | None) -> bool:
    """Return True when a local Transformers model looks materialized."""

    if not path:
        return False

    candidate = Path(path).expanduser()
    return candidate.is_dir() and (candidate / "config.json").is_file()


def resolve_model_source(
    *,
    local_path: str | Path | None,
    remote_id: str,
    allow_remote: bool = True,
) -> ModelSource:
    """Prefer the repo-local model and optionally fall back to Hugging Face."""

    if local_model_ready(local_path):
        return ModelSource(str(Path(local_path).expanduser()), True)

    if allow_remote:
        return ModelSource(remote_id, False)

    expected = Path(local_path).expanduser() if local_path else "<unset>"
    raise FileNotFoundError(
        "Silabs AI base model is not available locally at "
        f"{expected}. Run: python -m scripts.download_base_model"
    )
