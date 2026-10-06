from pathlib import Path

import pytest

from silabs_ai.model_source import local_model_ready, resolve_model_source


def test_local_model_is_preferred(tmp_path: Path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    source = resolve_model_source(
        local_path=model_dir,
        remote_id="remote/model",
        allow_remote=True,
    )

    assert source.is_local is True
    assert source.value == str(model_dir)
    assert local_model_ready(model_dir) is True


def test_remote_fallback_when_local_missing(tmp_path: Path):
    source = resolve_model_source(
        local_path=tmp_path / "missing",
        remote_id="remote/model",
        allow_remote=True,
    )

    assert source.is_local is False
    assert source.value == "remote/model"


def test_offline_mode_requires_local_model(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        resolve_model_source(
            local_path=tmp_path / "missing",
            remote_id="remote/model",
            allow_remote=False,
        )
