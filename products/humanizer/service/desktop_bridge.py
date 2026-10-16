"""Private JSON-lines protocol for the offline desktop workspace.

The desktop app launches this process locally. No web server, socket, account,
download, or network request is involved. Model instances are cached in RAM.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from .document_parser import export_docx_revisions, parse_document
from .rewrite import rewrite_text
from .style_profile import StyleProfile

_MODES = {"natural", "academic", "professional", "simplify", "grammar", "shorten", "expand"}
_models: dict[tuple[str, str], object] = {}


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
    if action == "open":
        parsed = parse_document(payload["path"])
        return {
            "path": str(parsed.path.resolve()),
            "name": parsed.path.name,
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
        if block is None or not block.editable or block.kind == "heading":
            raise ValueError("Selected block cannot be safely rewritten.")
        if len(block.text) > 5000:
            raise ValueError("Paragraph too long for safe rewriting (5000 characters maximum).")
        generate = _get_model(backend, model_path)
        start = time.perf_counter()
        proposal, review = rewrite_text(block.text, generate, StyleProfile(mode=mode))
        return {
            "index": block_index, "proposal": proposal, "passed": review.passed,
            "issues": review.issues, "elapsed_seconds": round(time.perf_counter() - start, 2),
        }

    if action == "export":
        source = Path(payload["path"]).resolve()
        target = Path(payload["destination"]).resolve()
        if source == target or target.exists():
            raise ValueError("Export must target a new, nonexistent file.")
        raw_revisions = payload.get("revisions", {})
        if not isinstance(raw_revisions, dict):
            raise ValueError("Revisions must be an object.")
        revisions = {int(k): v for k, v in raw_revisions.items()}
        original = parse_document(source)
        allowed = {b.index for b in original.blocks if b.editable and b.kind != "heading"}
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
    for line in sys.stdin:
        try:
            payload = json.loads(line)
            result = {"ok": True, "data": process(payload)}
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    serve()
