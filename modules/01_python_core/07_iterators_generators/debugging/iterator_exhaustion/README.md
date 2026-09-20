# Debug an exhausted amount iterator

## Difficulty

Intermediate

## Estimated time

20–30 minutes

## Observed symptom

`summarize_amounts` reports the right count but a zero total when it receives a one-shot generator.
Reiterable collections can hide the defect during casual testing.

## Reproduce

Run exactly:

`uv run pytest modules/01_python_core/07_iterators_generators/debugging/iterator_exhaustion -q --runxfail`

The starter is intentionally broken, so this command must fail before your change and pass after it.

## Allowed edit

Edit only
`modules/01_python_core/07_iterators_generators/debugging/iterator_exhaustion/broken.py`.

## Behavior that must remain

- `summarize_amounts` accepts any `Iterable[Decimal]`, including a one-shot generator.
- The result is a `(count, total)` tuple.
- Empty input returns count zero and `Decimal("0")` as its total.
- Arithmetic remains in `Decimal`; do not convert through `float`.

## Hints (optional)

A generator cannot be restarted after it is consumed. Trace each traversal of `amounts` and decide
how both output values can be derived safely for every iterable.

## Acceptance criteria

The reproduction command passes for the supplied generator, with both the exact count and exact
`Decimal` total, while the function continues to handle empty and reiterable inputs.

## Self-review checklist

- [ ] Did I reproduce the generator-specific failure first?
- [ ] Does the code work with a one-shot iterable?
- [ ] Are all monetary calculations still exact `Decimal` operations?
- [ ] Did I keep the public signature and tests unchanged?
