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


## GitHub Actions rebuild

The repository does not require the finalized JSONL corpus to be committed to Git.

Use the **Dataset Build and Smoke** workflow. Its build job:

1. downloads the public training sources from Hugging Face;
2. normalizes them into the canonical Silabs schema;
3. runs the v1.2 global normalized-input finalizer;
4. freezes SHA-256 release metadata and a deterministic 400/100 smoke subset;
5. validates the generated train/dev files; and
6. uploads the rebuilt corpus as a short-lived GitHub Actions artifact.

The workflow has two profiles:

- `research`: reproduces the historical eight-source research corpus;
- `commercial`: excludes sources currently marked noncommercial or requiring
  unresolved license review.

The research profile currently includes SciQ for research/evaluation only.
The commercial profile excludes SciQ and OpenBookQA until their intended use is
cleared under the applicable source terms.

Generated corpora remain outside normal Git history. Source identity and policy
are versioned in `datasets/registry/datasets.json`.
