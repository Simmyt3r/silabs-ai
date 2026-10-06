# Third-Party Components

Silabs AI uses third-party software, model weights and training datasets. Their licenses remain their own.

## Initial base model

`HuggingFaceTB/SmolLM2-360M-Instruct`

Before a release or commercial deployment, verify the current upstream model card, license text, attribution requirements and distribution conditions.

## Training datasets

The dataset registry intentionally requires current-source verification. An earlier local audit or remembered license is not enough for a new release.

## Python dependencies

See `requirements.txt`. A production release should retain a resolved dependency lockfile and software-bill-of-materials so the deployed environment is reproducible.
