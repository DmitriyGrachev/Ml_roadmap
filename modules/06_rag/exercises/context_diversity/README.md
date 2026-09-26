# Diversify retrieved museum evidence

Difficulty: Medium

## Prerequisites and time

Python sorting and counters, and the Module 06 retrieval/reranking lessons. Estimated time: 45–60 minutes.

## Goal and TODO boundary

Implement `select_evidence` to stop one museum document from filling the
context window. Validation and `Evidence` are supplied. Candidate authorization
has already occurred; this exercise handles ranking and source diversity only.

## Contract

- `Evidence(chunk_id, document_id, score)` contains nonblank exact string IDs
  and a finite Python integer or float score, excluding booleans. Negative scores
  are allowed. Chunk IDs must be unique across the whole input, even across
  different documents.
- `limit` is a nonnegative integer; `per_document` is a positive integer,
  default 1. Both reject booleans. Invalid arguments raise `ValueError`, even
  for empty candidates or zero limit.
- Rank by descending score, then ascending document ID, then ascending chunk ID.
  Input order does not break ties.
- Visit this ranking greedily. Accept a candidate only if its document has fewer
  than `per_document` accepted chunks. Stop once `limit` chunks are accepted.
- Return a tuple in ranking order. A result may be shorter than limit because of
  source caps. Empty input or zero limit returns `()`.
  Do not mutate candidates or retain state.
- Do not deduplicate different chunks by their text, rerank with a model, or
  enforce a token budget here.

## Hand-calculated example

Candidates a1/a/.9, a2/a/.8, b1/b/.7, c1/c/.6 with limit 3 and cap 1 yield
a1, b1, c1. The second chunk from a is skipped despite its higher score.
With tied scores, document a precedes b, and chunk a1 precedes a2.

## Optional hints

Keep a count for each accepted source. The global limit applies to accepted
candidates, not the number of visited rows.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/06_rag/exercises/context_diversity -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
