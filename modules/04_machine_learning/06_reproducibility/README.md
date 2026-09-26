# Reproducibility and artifact provenance

## Goal

Make a result traceable to exact inputs, environment, code, split and settings. Recognize
that model loading is a trust decision separate from checking evaluation quality.

## Java mental model

A trained artifact is not just a compiled class. It includes learned state whose meaning
depends on the feature schema and training environment. A checksum identifies bytes;
it does not establish who produced them or whether they are safe.

## Python model

Keep the lockfile, code revision, data checksum, feature schema, split definition,
hyperparameters and random seeds with the report. Record dependency versions. Use JSON
for human-reviewable metrics and metadata. It contains data rather than executable Python
objects, though applications must still validate the data they consume.

## Key concepts

- A seed does not pin input ordering, dependency versions or numerical implementations.
- Record development/validation/test provenance; do not reuse a test set for repeated selection.
- Never load untrusted pickle or joblib artifacts: deserialization can execute code.
- Load trusted models only in the documented environment; cross-version compatibility is not guaranteed.
- A hash detects a byte change, but authenticity needs a trusted source or signature.
- This module emits metadata only and does not serialize or load a model artifact.

References: [model persistence and trust](https://scikit-learn.org/stable/model_persistence.html)
and [controlling randomness](https://scikit-learn.org/stable/common_pitfalls.html#controlling-randomness).

## Example

```powershell
uv run python modules/04_machine_learning/06_reproducibility/example.py
```

The example fingerprints literal sensor CSV bytes and records a local experiment manifest.
It deliberately has no file-loading or pickle pathway. The exercise adds a complete
validated classification report and slice metrics.

## Exercises

Complete the [reproducible evaluation report](exercises/evaluation_report/README.md).
Explain which additional code revision and split information you would preserve alongside
that report in a real experiment.

## Self-check

1. Which changes can alter a result while keeping the same seed?
2. Why does a matching SHA-256 checksum not make an unknown pickle safe?
3. Why omit runtime timestamps from a deterministic report?

## Done when

You can produce a deterministic JSON-compatible report, identify its data and environment,
and explain the trust requirements before loading anyone else's trained artifact.
