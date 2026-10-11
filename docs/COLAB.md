# Silabs AI on Free Google Colab

This is the zero-cost GPU path for the current alignment smoke experiment.

## Important limitation

Google Colab is free to use, but free GPU access is not guaranteed and the
available GPU type can change. If Colab does not offer a GPU at a particular
time, try again later rather than running this training on CPU.

## Open the notebook

Repository notebook:

`notebooks/Silabs_AI_Alignment_Training.ipynb`

Open the file on GitHub and choose **Open in Colab**, or open Colab and load
the notebook from GitHub.

## Before running cells

In Colab:

```text
Runtime
→ Change runtime type
→ Hardware accelerator: GPU
→ Save
```

Then run the notebook cells from top to bottom.

The first cell verifies:

- CUDA is available;
- the GPU name;
- available VRAM;
- `nvidia-smi`.

If no GPU is available, the notebook stops immediately.

## What the notebook does

1. mounts Google Drive;
2. clones/pulls `Simmyt3r/silabs-ai`;
3. installs project dependencies while keeping Colab's CUDA PyTorch;
4. rebuilds the commercially screened dataset;
5. creates the 180-record balanced public subset;
6. adds 45 benchmark-disjoint Silabs alignment records;
7. verifies zero evaluation-prompt leakage and zero train/dev overlap;
8. downloads the SmolLM2 base model;
9. runs base compact, v2 capability and raw-safety evaluations;
10. trains the LoRA adapter on the Colab GPU;
11. evaluates the candidate on all three suites;
12. applies zero-regression promotion gates;
13. copies reports to Google Drive.

## Persistent files

The adapter is written directly to:

```text
MyDrive/SilabsAI/outputs/silabs-ai-v1-alignment-smoke
```

Reports and manifests are copied to:

```text
MyDrive/SilabsAI/results
```

Training checkpoints are saved every 10 steps, with at most two retained.
This reduces the amount of work lost if a free Colab runtime disconnects.

## Promotion policy

A Colab-trained candidate is judged by the same policy as every other
candidate:

- compact behavior >= 95%;
- corrected capability v2 >= 84%;
- raw safety >= 33.3%;
- zero compact regressions;
- zero capability regressions;
- zero raw-safety regressions.

Automated gate success still requires manual review before promotion.
