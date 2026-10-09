# Evaluation

Silabs AI uses behavioral evaluation as a promotion gate. Training loss is useful for optimization, but it does not prove that a model became more useful.

## Baseline suite

The deterministic suite in `evaluation/cases.jsonl` covers:

- conversation stability;
- Silabs identity behavior;
- arithmetic;
- simple reasoning;
- basic science;
- instruction following;
- coding fundamentals;
- repetition/degeneration.

Run the untouched base model after materializing it locally:

```bash
python -m scripts.download_base_model
python -m evaluation.run_eval --offline --report-name baseline_smollm2_360m.json
```

Reports are written under `reports/` and are not committed to Git. The GitHub
`Baseline Evaluation` workflow uploads the report as a workflow artifact so a
specific run can be retained without polluting source history.

## Scoring

Cases may specify:

- `exact`: normalized exact match;
- `must_contain`: required substrings;
- `must_not_contain`: banned substrings;
- `must_match`: required regular expressions;
- `min_words` / `max_words`: response-length constraints.

Every case also receives a repeated 4-gram degeneration check.

The report contains the overall pass rate, category pass rates, token counts,
latency, generated output and failure reasons.

## Comparing candidates

For a local candidate checkpoint:

```bash
python -m evaluation.run_eval --model outputs/silabs-ai-v1 --offline --report-name candidate.json
```

Passing the suite is necessary but not sufficient for promotion. A candidate
must also receive manual review and broader academic, safety and domain testing.


## Expanded capability suite

`evaluation/cases_extended.jsonl` contains 50 deterministic cases covering
conversation, Silabs identity, strict instruction following, arithmetic,
reasoning, science, coding, robustness and short academic responses.

Use it for candidate decisions rather than relying only on the original
20-case regression suite:

```bash
python -m evaluation.run_eval \
  --cases evaluation/cases_extended.jsonl \
  --offline \
  --report-name capability_50.json
```

## Safety and uncertainty suite

`evaluation/cases_safety.jsonl` is evaluated separately. It covers privacy,
credential theft, phishing, malware/ransomware, urgent medical escalation,
medical uncertainty, financial guarantees, legal certainty and fabrication of
unknown/future claims.

A separate score prevents capability gains from hiding safety regressions.

## Promotion gates

`evaluation/promotion_gate.py` can require:

- a minimum absolute candidate score;
- a minimum score delta over the baseline; and
- a maximum number of per-case regressions.

For release decisions, `evaluation/release_gate.py` combines independent
capability and safety comparison reports. A release candidate must satisfy both
domains. The default engineering policy is zero behavioral regressions unless
an explicit reviewed exception is recorded.

Passing automated gates is still not sufficient for release. Manual response
quality review remains mandatory before a named Silabs AI version is promoted.
