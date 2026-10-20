"""Private JSON-lines protocol for the offline desktop workspace.

The desktop app launches this process locally. No web server, socket, account,
download, or network request is involved. Model instances are cached in RAM.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

from .document_parser import export_docx_revisions, parse_document
from .rewrite import rewrite_text
from .style_profile import StyleProfile

_MODES = {"natural", "academic", "professional", "simplify", "grammar", "shorten", "expand"}
_models: dict[tuple[str, str], object] = {}


def _fingerprint(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _verify_source(payload: dict) -> None:
    expected = payload.get("fingerprint")
    if not isinstance(expected, str) or _fingerprint(payload["path"]) != expected:
        raise ValueError("Source document changed since opening. Reopen it before applying edits.")


def _get_model(backend: str, model_path: str):
    key = (backend, str(Path(model_path).expanduser().resolve()))
    if key not in _models:
        if backend == "gguf":
            from .local_model import GGUFLocalModel
            _models[key] = GGUFLocalModel(key[1], max_new_tokens=512)
        elif backend == "transformers":
            from .local_model import TransformersLocalModel
            _models[key] = TransformersLocalModel(key[1], max_new_tokens=512)
        else:
            raise ValueError("Invalid local model backend.")
    return _models[key]


def process(payload: dict) -> dict:
    action = payload.get("action")
    if action == "diagnostics":
        # Inspect only local files/dependencies; never load weights, download
        # models, or inspect user documents during a setup check.
        value = payload.get("model_path")
        model = Path(value).expanduser() if isinstance(value, str) and value.strip() else None
        file_exists = bool(model and model.is_file())
        header_ok = False
        model_bytes = 0
        if file_exists and model is not None:
            model_bytes = model.stat().st_size
            with model.open("rb") as stream:
                header_ok = stream.read(4) == b"GGUF"
        gguf_valid = file_exists and header_ok and model_bytes >= 100_000_000
        inference_installed = importlib.util.find_spec("llama_cpp") is not None
        docs_installed = importlib.util.find_spec("docx") is not None
        # An installed Python package does not guarantee its data survived
        # PyInstaller. Exercise a real lookup in the extracted wordfreq list.
        english_dictionary_installed = False
        try:
            from wordfreq import zipf_frequency
            english_dictionary_installed = zipf_frequency("language", "en") > 0
        except (ImportError, LookupError, OSError, ValueError):
            english_dictionary_installed = False
        issues = []
        if not gguf_valid:
            issues.append("Local GGUF weights not found or invalid. Check Model settings.")
        if not inference_installed:
            issues.append("Local llama.cpp inference components are missing. Reinstall the offline edition.")
        if not docs_installed:
            issues.append("Word document support is missing. Reinstall the offline edition.")
        if not english_dictionary_installed:
            issues.append("Offline English spelling dictionary is unavailable. Reinstall the complete edition.")
        return {
            "components_present": bool(gguf_valid and inference_installed and docs_installed and english_dictionary_installed),
            "model_file_found": file_exists,
            "gguf_header_valid": header_ok,
            "model_bytes": model_bytes,
            "inference_installed": inference_installed,
            "word_support_installed": docs_installed,
            "english_dictionary_installed": english_dictionary_installed,
            "issues": issues,
            "note": "File and component checks only; model load and rewrite quality are not tested.",
        }

    if action == "analyse_writing":
        from .offline_review import analyse_writing
        return analyse_writing(payload.get("text", ""), spelling=payload.get("spelling", True))

    if action == "compare_local_sources":
        from .local_similarity import compare_local_sources
        _verify_source(payload)
        parsed = parse_document(payload["path"])
        overrides = payload.get("revisions", {})
        if not isinstance(overrides, dict):
            raise ValueError("Document revisions must be an object.")
        blocks = []
        valid = {b.index for b in parsed.blocks if b.editable}
        for key, replacement in overrides.items():
            index = int(key)
            if index not in valid or not isinstance(replacement, str):
                raise ValueError("Invalid working-copy revision.")
        for block in parsed.blocks:
            value = overrides.get(str(block.index), block.text)
            if value.strip():
                blocks.append(value)
        return compare_local_sources(
            "\n".join(blocks),
            payload.get("sources", []),
            source_document=payload["path"],
        )

    if action == "open":
        parsed = parse_document(payload["path"])
        return {
            "path": str(parsed.path.resolve()),
            "name": parsed.path.name,
            "fingerprint": _fingerprint(parsed.path),
            "format": parsed.path.suffix.lower().lstrip("."),
            "blocks": [
                {
                    "index": b.index, "kind": b.kind, "text": b.text,
                    "style": b.style, "editable": b.editable, "reason": b.reason,
                }
                for b in parsed.blocks
            ],
        }

    if action == "rewrite":
        _verify_source(payload)
        path = payload["path"]
        block_index = payload["index"]
        mode = payload.get("mode", "natural")
        backend = payload.get("backend", "gguf")
        model_path = payload["model_path"]
        if not isinstance(block_index, int) or isinstance(block_index, bool):
            raise ValueError("Block index must be an integer.")
        if mode not in _MODES:
            raise ValueError("Unknown rewrite mode.")
        parsed = parse_document(path)
        block = next((b for b in parsed.blocks if b.index == block_index), None)
        if block is None or not block.editable:
            raise ValueError("Selected block cannot be safely rewritten.")
        working_text = payload.get("text", block.text)
        if not isinstance(working_text, str) or not working_text.strip():
            raise ValueError("Select or type text before requesting a suggestion.")
        if len(working_text) > 5000:
            raise ValueError("Selection too long for a single rewrite (5000 characters maximum).")
        generate = _get_model(backend, model_path)
        start = time.perf_counter()
        proposal, review = rewrite_text(working_text, generate, StyleProfile(mode=mode))
        return {
            "index": block_index, "proposal": proposal, "passed": review.passed,
            "issues": review.issues, "elapsed_seconds": round(time.perf_counter() - start, 2),
        }

    if action == "export":
        _verify_source(payload)
        source = Path(payload["path"]).resolve()
        target = Path(payload["destination"]).resolve()
        if source == target or target.exists():
            raise ValueError("Export must target a new, nonexistent file.")
        raw_revisions = payload.get("revisions", {})
        if not isinstance(raw_revisions, dict):
            raise ValueError("Revisions must be an object.")
        revisions = {int(k): v for k, v in raw_revisions.items()}
        original = parse_document(source)
        allowed = {b.index for b in original.blocks if b.editable}
        for index, value in revisions.items():
            if index not in allowed or not isinstance(value, str) or not value.strip():
                raise ValueError(f"Invalid revision for block {index}.")
        if source.suffix.lower() == ".docx":
            export_docx_revisions(source, target, revisions)
        elif source.suffix.lower() in (".txt", ".md"):
            # Plain-text paragraph indices follow the exact split contract.
            raw = source.read_bytes().decode("utf-8")
            sep = "\r\n\r\n" if "\r\n\r\n" in raw else "\n\n"
            paragraphs = raw.split(sep)
            keys = [i for i, text in enumerate(paragraphs) if text.strip()]
            if len(keys) != len(original.blocks):
                raise ValueError("Text file structure changed since import.")
            for idx, proposed in revisions.items():
                paragraphs[keys[idx]] = proposed
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(sep.join(paragraphs).encode("utf-8"))
        else:
            raise ValueError("Unsupported export format.")
        return {"destination": str(target), "revised_count": len(revisions)}

    raise ValueError(f"Unknown action: {action}")


def serve() -> None:
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="strict")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    for line in sys.stdin:
        try:
            payload = json.loads(line)
            result = {"ok": True, "data": process(payload)}
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        # Escape non-ASCII on the protocol. This stays valid UTF-8 even on
        # Windows computers with legacy console code pages (e.g. CP1252).
        sys.stdout.write(json.dumps(result, ensure_ascii=True) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    serve()
