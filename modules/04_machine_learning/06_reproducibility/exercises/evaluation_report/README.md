# Reproducible evaluation report

Difficulty: Medium

Estimated time: 60–75 minutes. Prerequisites: classification metrics and reproducibility lessons.

A greenhouse classifier estimates whether a plant needs watering. Produce a reviewable
report from already-frozen predictions, including overall metrics and shade/sun slices.
This boundary performs evaluation only: it neither trains a model nor loads an artifact.

## Contract

Implement `build_evaluation_report` using the supplied `TypedDict` interfaces:

1. Require equal nonzero lengths for labels, probabilities and slice labels. Labels
   are 0/1; probabilities and threshold are finite numbers in `[0, 1]`. Every slice
   label and `model_name` must be a nonempty, non-whitespace string. Preserve their text.
2. Require a nonnegative integer seed and a SHA-256 string of exactly 64 hexadecimal
   characters. Normalize the checksum to lowercase. Reject invalid inputs with `ValueError`
   naming the invalid field (`length`, `label`, `probability`, `slice`, `threshold`,
   `checksum`, `seed` or `model`).
3. Classify as positive when `probability >= threshold`, including equality.
4. Overall and each observed slice return exactly `count`, `accuracy`, `precision`,
   `recall`, `f1`, `brier`. Use zero for undefined precision/recall/F1, including
   slices containing no positives. Brier is the mean of `(probability - label) ** 2`.
   Use unrounded native Python numbers; `count` is an integer.
5. Include `schema_version=1`, supplied model name/seed/normalized checksum/threshold,
   `metrics`, and `slices` with lexicographically ordered keys. Include exactly three
   `versions` keys: `python` (`platform.python_version()`), `numpy`, `scikit_learn`.
6. Do not mutate inputs, add timestamps, perform file/network I/O or serialize/load models.
   Identical inputs in the same environment produce an identical JSON-compatible dict.
   `json.dumps(report, sort_keys=True, allow_nan=False)` must succeed.

Example: for labels `[0, 1, 1, 0]` and probabilities `[0.1, 0.8, 0.4, 0.7]` at threshold
`0.5`, accuracy/precision/recall/F1 are each `0.5`; Brier is `0.225`.

## Edge cases

A slice with no positives, no predicted positives, equality at threshold, single-row
slices, empty/mismatched sequences, nonfinite probabilities and malformed provenance.
Slice metrics diagnose behavior; they do not establish significance from tiny samples.

## Run

```powershell
uv run pytest modules/04_machine_learning/06_reproducibility/exercises/evaluation_report -q
```

Done when the report passes all tests and you can explain why a checksum plus a good
score still gives no permission to load an unknown pickle. Save the code revision,
feature schema and split specification alongside this report in a real experiment.
