# Evaluation

Разбор качества, задержки и стоимости: [теория урока](theory.md).

## Goal

Make a release decision from explicit quality, latency, and cost criteria instead of a few
convincing demonstrations.

## Java mental model

Contract tests resemble ordinary unit tests. A golden dataset resembles a versioned
acceptance corpus with expected behavior and a scoring rubric. Passing the former cannot
substitute for measuring the latter against the real model and prompt version.

## Python model

Keep case IDs, inputs, expected outcomes, and measured predictions separate. Join by ID;
reject missing or duplicated records rather than silently shrinking the denominator. Treat
refusal as an explicit outcome, not an empty string that accidentally passes validation.

## Key concepts

Define the task's success criteria before choosing metrics. Build a representative golden
set containing ordinary queries, ambiguous inputs, missing evidence, required refusals, and
adversarial reference text. Use development cases for prompt changes and preserve held-out
cases for a later check. Reusing a holdout to tune repeatedly turns it into development data.
See [Anthropic's evaluation guidance](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
for task-specific success criteria and grading approaches.

Exact matching works for narrow facts and labels. It is too brittle for open-ended prose;
use a documented rubric, human review, or a calibrated evaluator there. A model-based judge
has errors and biases of its own. Track answerable and refusal-required slices separately:
an assistant that refuses everything may look strong on refusal cases alone.

Report sample counts alongside rates, mean and tail latency, and total/average cost. Small
sets and one stochastic run give limited evidence; use repeated runs when variability
matters. Record model, prompt, data, and grading versions. A release can require a quality
floor and both latency and cost ceilings instead of maximizing one number.

## Example

```powershell
uv run python modules/05_llm_engineering/05_evaluation/example.py
```

Three invented trial summaries illustrate an explicit acceptance policy. The fastest
candidate misses the quality floor, while the most accurate misses the latency ceiling.

## Exercises

Implement the Medium [Library answer evaluation](exercises/answer_evaluation/README.md),
including ID alignment, refusal slices, nearest-rank p95, and decimal cost totals.

## Self-check

1. Why do missing predictions invalidate a comparison?
2. What does an absent slice mean, and why is zero a misleading score for it?
3. Why might a prompt improve development results and fail on a held-out set?

## Done when

Your offline scorer passes its arithmetic and validation tests, and you can distinguish
that result from measuring quality on representative outputs of a real model.
