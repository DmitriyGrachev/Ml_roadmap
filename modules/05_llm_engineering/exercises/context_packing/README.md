# Priority-aware library context packing

Difficulty: Medium

## Prerequisites and time

Python sorting, immutable records, and the Module 05 context-budget lesson. Estimated time: 45–60 minutes.

## Goal and TODO boundary

Implement `pack_context` to choose supplied library reference segments within a
known token allowance. Validation and result types are provided. Costs are supplied
integers; do not tokenize text or call a model.

## Contract

- Each `ContextSegment(id, text, tokens, priority)` has a unique nonblank string
  ID, any string text (including empty), positive integer tokens, and an integer
  priority (negative values allowed). Preserve exact strings.
- `budget` is a nonnegative integer; `reserved` is an integer from 0 through
  budget. Neither numeric fields nor budget parameters accept booleans.
  Invalid inputs raise `ValueError`, including at zero available capacity.
- Available capacity is `budget - reserved`. Visit candidates by descending
  priority, retaining original input order for equal priorities.
- Greedily select a segment if its full token cost fits the remaining capacity.
  Skip one that does not fit and continue visiting later candidates. Do not split
  segments, recompute their costs, or optimize a knapsack objective.
- Return `PackedContext(segments, used_tokens)`. Selected segments must be
  restored to **original input order** for coherent context reading. Token usage
  is their supplied cost sum; no implicit separator cost is added.
- Empty input or zero capacity returns `PackedContext((), 0)`.
  Do not mutate inputs or retain state across calls.

## Hand-calculated example

Input segments A=(2 tokens, priority 1), B=(3, 9), C=(2, 5), budget 6, reserved 1
give capacity 5. B is considered first, C second, and A no longer fits.
Return B then C with used_tokens 5. If all three fit, return A, B, C despite
the different selection order.

## Optional hints

Carry original positions through priority sorting. Selection order and final
context order serve different purposes.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/05_llm_engineering/exercises/context_packing -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
