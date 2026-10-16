"""Offline Humanizer CLI pilot.

Usage:
  python -m products.humanizer.service.cli \
    --input thesis.docx --output thesis-revised.docx \
    --backend gguf --model ./models/qwen3-1.7b-q4.gguf --limit 3

Rewrites safe body paragraphs into a new DOCX. No in-place changes.
"""
from __future__ import annotations

import argparse

from .document_parser import export_docx_revisions, parse_document
from .rewrite import rewrite_text
from .style_profile import StyleProfile


def main() -> int:
    parser = argparse.ArgumentParser(description="Silabs Humanizer offline DOCX pilot")
    parser.add_argument("--input", required=True, help="Source DOCX file")
    parser.add_argument("--output", required=True, help="New destination DOCX file")
    parser.add_argument("--model", required=True, help="Local GGUF file or local Transformers directory")
    parser.add_argument("--backend", choices=("gguf", "transformers"), default="gguf")
    parser.add_argument("--mode", choices=("natural", "academic", "professional", "simplify"), default="natural")
    parser.add_argument("--limit", type=int, default=3, help="Maximum paragraphs to attempt (default 3)")
    parser.add_argument("--include-tables", action="store_true", help="Also rewrite safe table cell paragraphs")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cpu", help="Transformers backend only")
    parser.add_argument("--dtype", choices=("float32", "float16", "bfloat16", "auto"), default="float32")
    parser.add_argument("--gpu-layers", type=int, default=0, help="llama.cpp GPU layers; zero = CPU")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be >= 1")

    from pathlib import Path
    source_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if source_path == output_path:
        parser.error("Output must be a different file; overwriting originals is forbidden.")
    if output_path.exists():
        parser.error(f"Output already exists: {output_path}")

    doc = parse_document(args.input)
    if doc.path.suffix.lower() != ".docx":
        parser.error("This pilot currently exports DOCX only.")
    if args.backend == "gguf":
        from .local_model import GGUFLocalModel
        generate = GGUFLocalModel(args.model, gpu_layers=args.gpu_layers)
    else:
        from .local_model import TransformersLocalModel
        generate = TransformersLocalModel(args.model, device=args.device, dtype=args.dtype)

    proposed: dict[int, str] = {}
    attempts = 0
    for block in doc.blocks:
        if attempts >= args.limit:
            break
        if not block.editable or block.kind == "heading" or (block.kind == "table_cell" and not args.include_tables):
            continue
        attempts += 1
        revised, review = rewrite_text(block.text, generate, StyleProfile(mode=args.mode))
        if not review.passed:
            print(f"SKIP block {block.index}: {', '.join(review.issues)}")
            continue
        proposed[block.index] = revised
        print(f"PROPOSE block {block.index} ({len(block.text)} -> {len(revised)} chars)")

    if not proposed:
        print("No safe revisions generated. Original document remains unchanged.")
        return 2
    destination = export_docx_revisions(doc.path, args.output, proposed)
    print(f"Saved {len(proposed)} proposed paragraph revisions to {destination}")
    print("Review the new document manually before using it; meaning preservation is not yet automatically verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
