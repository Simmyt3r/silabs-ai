from __future__ import annotations

import argparse
import subprocess

import torch


def gib(value: int) -> float:
    return value / (1024 ** 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a CUDA GPU for Silabs AI training")
    parser.add_argument("--min-vram-gb", type=float, default=8.0)
    args = parser.parse_args()

    print("torch:", torch.__version__)
    print("cuda build:", torch.version.cuda)
    print("cuda available:", torch.cuda.is_available())

    if not torch.cuda.is_available():
        raise SystemExit("GPU VALIDATION FAIL: torch.cuda.is_available() is False")

    count = torch.cuda.device_count()
    print("cuda devices:", count)
    if count < 1:
        raise SystemExit("GPU VALIDATION FAIL: no CUDA devices found")

    for index in range(count):
        props = torch.cuda.get_device_properties(index)
        total_gb = gib(props.total_memory)
        print(f"gpu[{index}]: {props.name}")
        print(f"gpu[{index}] compute capability: {props.major}.{props.minor}")
        print(f"gpu[{index}] vram_gb: {total_gb:.2f}")

    primary = torch.cuda.get_device_properties(0)
    primary_gb = gib(primary.total_memory)
    if primary_gb < args.min_vram_gb:
        raise SystemExit(
            f"GPU VALIDATION FAIL: {primary.name} has {primary_gb:.2f} GiB VRAM; "
            f"{args.min_vram_gb:.2f} GiB required"
        )

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            check=True,
            text=True,
            capture_output=True,
        )
        print("nvidia-smi:")
        print(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"GPU VALIDATION FAIL: nvidia-smi unavailable: {exc}") from exc

    x = torch.randn((1024, 1024), device="cuda", dtype=torch.float16)
    y = x @ x
    torch.cuda.synchronize()
    print("fp16 smoke tensor:", tuple(y.shape), y.dtype)
    print("GPU VALIDATION PASS")


if __name__ == "__main__":
    main()
