from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from silabs_ai.config import get_settings
from silabs_ai.model_source import local_model_ready


def run(*args: str) -> None:
    command = [sys.executable, *args]
    print("\n$", " ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Silabs AI v1 smoke-training pipeline end to end"
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="Rebuild final_v0_1 from prepared per-dataset JSONL before preflight.",
    )
    parser.add_argument(
        "--release-name",
        default="silabs-v1",
        help="Dataset release name written into the release manifest.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    train = root / "datasets" / "processed" / "final_v0_1" / "train.jsonl"
    dev = root / "datasets" / "processed" / "final_v0_1" / "dev.jsonl"

    if args.finalize:
        run("-m", "scripts.finalize_training_data_v1_2")

    if not train.exists() or not dev.exists():
        raise SystemExit(
            "Missing finalized corpus. Expected:\n"
            f"  {train}\n"
            f"  {dev}\n"
            "Restore those ignored local files, or use --finalize when the "
            "prepared per-dataset JSONL files are present."
        )

    settings = get_settings()
    if not local_model_ready(settings.model_path):
        print("Local base model is missing; downloading it now.")
        run("-m", "scripts.download_base_model")

    run(
        "-m",
        "scripts.preflight",
        "--train",
        str(train),
        "--dev",
        str(dev),
    )

    run(
        "-m",
        "scripts.freeze_dataset_release",
        "--train",
        str(train),
        "--dev",
        str(dev),
        "--name",
        args.release_name,
        "--manifest",
        f"datasets/registry/releases/{args.release_name}.json",
    )

    run(
        "-m",
        "evaluation.run_eval",
        "--offline",
        "--report-name",
        "baseline_smollm2_360m.json",
    )

    run(
        "-m",
        "training.train_sft",
        "--config",
        "configs/smollm2-360m-smoke.yaml",
    )

    run(
        "-m",
        "evaluation.run_eval",
        "--model",
        "outputs/silabs-ai-v1-smoke",
        "--offline",
        "--report-name",
        "smoke_candidate.json",
    )

    run(
        "-m",
        "evaluation.compare_reports",
        "reports/baseline_smollm2_360m.json",
        "reports/smoke_candidate.json",
        "--output",
        "reports/smoke_comparison.json",
    )

    print("\nSILABS AI SMOKE PIPELINE COMPLETE")
    print("Review reports/smoke_comparison.json before any full-corpus run.")


if __name__ == "__main__":
    main()
