# Fraud probability after an alert

## Goal

Use conditional probability to interpret a fraud alert when fraud itself is rare.

## Difficulty

Intermediate.

## Estimated time

25–40 minutes.

## Requirements

Implement `fraud_probability_given_alert(base_rate, sensitivity,
false_positive_rate)` in `starter.py`. Each input must be finite and inside `[0, 1]`.
Return the posterior probability that a transaction is fraudulent given that the alert
fired. If the total probability of an alert is zero, raise `ValueError`; the conditional
probability is undefined in that case.

Before coding, substitute these supplied banking-alert rates into Bayes' rule on paper:

- fraud base rate: `0.001`;
- alert sensitivity: `0.95`;
- alert false-positive rate: `0.01`.

Keep that substitution with your learning notes, then use the tests to check the code.

## Acceptance criteria

The rare-event example returns the tested posterior within floating-point tolerance.
Every argument rejects values below zero, above one, `NaN`, and either infinity. A zero
total alert probability raises a clear `ValueError` rather than returning an invented
zero.

## Commands

Run from the repository root:

```powershell
uv run pytest modules/03_data_foundations/04_practical_statistics/exercises/bayes_alert -q -rx
```

## Hints

Write the probability of a true alert and the probability of a false alert as separate
terms. Their sum is the probability of observing any alert. Validate all three inputs
before dividing.
