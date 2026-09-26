# Guard query-level retrieval regressions

Difficulty: Medium

## Prerequisites and time

Python dictionaries and sets, recall at k, and the Module 06 retrieval-evaluation lesson. Estimated time: 60–75 minutes.

## Goal and TODO boundary

Implement `compare_retrieval` to compare baseline and candidate retrieval on
the same supplied query judgments. Validation and result records are provided.
Use local document IDs; no embeddings, evaluator model, or external service is needed.

## Contract

- Each `QueryJudgment(query_id, relevant_ids)` has a unique nonblank query ID
  and a frozenset of nonblank relevant document IDs. Exact strings are preserved.
  An empty relevant set is valid.
- Baseline and candidate are dictionaries of query ID to ranked document-ID
  tuples. Ranking keys must belong to the judgments; missing judged queries are
  treated as empty rankings. Ranked IDs must be nonblank strings. Unknown document
  IDs are valid misses; duplicate ranked IDs are allowed.
- `k` is a positive integer, excluding bool. `max_query_drop` and
  `max_mean_drop` are finite numbers in [0, 1], excluding bool, defaulting to 0.
  Invalid judgments, rankings, or policy inputs raise `ValueError`.
- For each ranking remove repeated document IDs while preserving first occurrence,
  **then** keep its first k unique IDs. Recall is the number of relevant IDs in
  this prefix divided by the full relevant-set size. Empty relevant sets score 0.
- Include **every judgment** in both macro-mean denominators, including missing
  rankings and queries with empty relevant sets. Do not average only answered,
  improved, or answerable queries. Empty judgments give both means 0.
- A query regresses when `baseline_recall - candidate_recall` exceeds
  `max_query_drop + 1e-12`; return regressed IDs in ascending order.
  The 1e-12 tolerance only prevents floating-point boundary noise.
- The overall guard passes when there are no regressed queries **and**
  `baseline_mean - candidate_mean <= max_mean_drop + 1e-12`.
  Empty evaluation passes.
- Return `RegressionReport(query_count, baseline_mean, candidate_mean,
  regressed_queries, passed)` without rounding or changing inputs.

## Hand-calculated example

Query hours has relevant {a,b}: baseline retrieves a,b, candidate retrieves a.
Query map has relevant {c}: baseline is missing, candidate retrieves c.
At k=2, baseline mean is (1+0)/2 = .5 and candidate mean is (.5+1)/2 = .75.
With zero allowed query drop, hours regresses and the guard fails despite a better
overall mean.

## Optional hints

Evaluate a pair of scores for every judgment first. Apply query and mean guards
separately; an average can hide a specific query regression.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/06_rag/exercises/retrieval_regression -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
