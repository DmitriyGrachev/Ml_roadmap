# Reciprocal rank fusion

Difficulty: Medium

Estimated time: 45–60 minutes. Prerequisites: mappings, sorting and hybrid retrieval lesson.

Combine lexical and vector candidate lists for local trail guides. The caller must
authorize each list before this function and recompute ranks; this function grants no access.

## Contract

- Every list contains nonblank document IDs, unique within that list. IDs may appear in
  several lists. Preserve exact spelling. Reject duplicates rather than silently counting
  them twice or shifting later ranks.
- Ranks are one-based. A document receives `weight / (rank_constant + rank)` from each
  list containing it. Missing appearances contribute zero. Sum contributions before sorting.
- Default weights are one per list. Supplied weights must match list count, be finite
  and lie in `[0, 1]`. A zero-weight list contributes no candidates. All-zero weights
  are allowed and yield `()`. Validate zero-weight lists too.
- Require a finite strictly positive `rank_constant` and a nonnegative integer `top_k`
  that is not a boolean. Validate all input even if `top_k=0`.
- Return `tuple[FusedHit, ...]` sorted by descending score, then ascending document ID
  for exact ties. Do not round scores internally. Return at most `top_k` records.
- No lists, empty lists or no positive-weight candidates produce `()`. Do not mutate
  caller-owned rankings or weights. Invalid inputs raise `ValueError` naming `document`,
  `weight`, `rank_constant` or `top_k`.

The bounded weights keep this exercise's scale explicit; production weighted-RRF
implementations may support different weight ranges. RRF's rank constant is separate
from the final result count `top_k`.

## Edge cases

Consensus across lists, unequal weights, one-based rank errors, exact ties, duplicate
IDs within one list, empty branches, a disabled branch and invalid nonfinite settings.

## Run

```powershell
uv run pytest modules/06_rag/04_hybrid_reranking/exercises/reciprocal_rank_fusion -q
```

Done when scores and ordering match the contract and you can explain why fusion is
not a calibrated relevance probability or a substitute for reranking evaluation.
