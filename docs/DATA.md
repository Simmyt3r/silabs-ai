# Data Governance

Silabs AI training data must be traceable, validated and license-reviewed.

## Do not commit large data artifacts

The repository excludes raw datasets, processed training corpora, model weights, checkpoints and local indexes. Git should hold the code and metadata needed to reproduce a training run.

## Preferred JSONL schema

```json
{"messages":[{"role":"user","content":"Question"},{"role":"assistant","content":"Answer"}],"meta":{"source":"dataset-name","split":"train"}}
```

The current loader also accepts instruction/output, prompt/response, question/answer and input/output pairs while older data is migrated.

## Release checks

Before a corpus is approved:

1. parse every record;
2. reject empty or malformed conversations;
3. detect exact duplicates;
4. check train/dev overlap;
5. review semantic and benchmark leakage;
6. audit suspicious repetition and answer quality;
7. compare source counts with the release manifest;
8. verify current source licenses;
9. record transformations and dataset version.

## Dataset registry

`datasets/registry/datasets.json` tracks intended sources. Entries marked `VERIFY_CURRENT_SOURCE` require an authoritative license/source check before the next approved commercial training release.
