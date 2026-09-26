# Nature-guide context budget

Difficulty: **Medium**. Theme: selecting complete nature-guide excerpts for a question.

## Goal

Implement `pack_context` with explicit output reservation, deterministic selection, and
traceable omissions, without silently cutting documents.

## Java mental model

This is a bounded resource allocator with an injected sizing strategy. Priority order is
provided by the caller; the exercise does not implement search, ranking, or a knapsack solver.

## Python model

Return the provided `PackedContext`: an immutable tuple of selected `Document` records,
an ordered tuple of dropped identifiers, and an integer `input_tokens` accounting total.
The name reflects the intended adapter boundary; unit tests also use synthetic counters.

## Key concepts

Inputs are typed integers and documents. Require `context_limit > 0`, `reserved_output >= 0`,
`overhead >= 0`, and `reserved_output + overhead <= context_limit`. On failure raise
`ValueError` mentioning `budget`, `limit`, `reserved`, or `overhead`. The caller includes
instructions, question, document metadata, and framing estimates in `overhead`.

Require nonblank, exact-unique document identifiers; errors mention `identifier` or
`document`. Preserve valid identifiers and text verbatim. Empty text is allowed.

For valid inputs, call `count_tokens(document.text)` exactly once per document, in original
order. The counter supplies nonnegative integer costs; reject negative values with
`ValueError` mentioning `count` or `token`. Begin input usage at `overhead`. Include a whole
document when its cost fits the remaining input budget, including exact equality; otherwise
record its ID and continue considering later documents. Zero-cost text may fit a zero
remainder. Return usage including overhead but **excluding** reserved output. Never mutate
inputs or truncate text.

This exercise explicitly assumes additive supplied costs. `len` counts Python characters
for predictable test fixtures; it is **not** a billed-token counter. A real adapter must
measure the final serialized request with the model's tokenizer/accounting rules, allow for
non-additivity and framing, then recheck limits before sending.

## Example

With limit 12, reserved output 3, overhead 2, and document costs 4, 3, 1, select the first
two documents. Input usage is 9 and the third ID is dropped. For costs 8, 2, 3 with five
units remaining, skip the first and select the latter two without reordering.

## Exercises

Implement the boundary and run:

```powershell
uv run pytest modules/05_llm_engineering/04_context_and_cost/exercises/context_budget
```

Tests include a counter whose costs differ from character length, exact fits, skipped
documents, zero-cost input, invalid budgets, and preservation of complete source text.

## Self-check

1. Why must the loop continue after an oversized excerpt?
2. Why is reserved output excluded from reported input usage?

## Done when

All tests pass with zero xfails and you can state the additional counting work required
before using this application policy with a real provider.
