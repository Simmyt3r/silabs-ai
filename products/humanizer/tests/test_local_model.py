import pytest

from products.humanizer.service.local_model import GGUFLocalModel, TransformersLocalModel


def test_gguf_missing_model_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        GGUFLocalModel(tmp_path / "missing.gguf")


def test_transformers_missing_model_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        TransformersLocalModel(tmp_path / "nonexistent")


def test_transformers_empty_directory_fails_closed(tmp_path):
    path = tmp_path / "empty"
    path.mkdir()
    with pytest.raises(FileNotFoundError):
        TransformersLocalModel(path)
