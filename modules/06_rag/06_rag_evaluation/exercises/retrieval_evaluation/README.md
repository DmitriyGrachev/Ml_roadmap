# Retrieval evaluation by query

Difficulty: Medium

Estimated time: 60–75 minutes. Prerequisites: retrieval evaluation lesson, mappings and logarithms.

Evaluate local library and park queries using frozen relevance judgments. Join by query
ID rather than row order, and include unsuccessful queries in the aggregate.

## Contract

- `judgments` is a nonempty mapping from query ID to `{document_id: relevance_grade}`.
  Query/document IDs are nonblank strings. Grades are integers in `0..3`; reject booleans.
  An empty inner mapping is allowed. Positive grades indicate relevant documents.
- `results` maps declared query IDs to ranked document IDs. A missing query means an
  empty retrieval run. Unknown result query IDs are invalid. Returned document IDs
  must be nonblank and unique within their whole list, including entries beyond k.
  Unjudged documents are allowed and receive grade zero for that query.
- `k` must be a positive integer, not a boolean. Invalid input raises `ValueError`
  mentioning `query`, `document`, `grade` or `k`. Validate the entire input before slicing.
- For each declared query, consider only its first k results. Return `QueryMetrics`:
  `relevant_total` counts positive judgments across the whole query's judgment set;
  `retrieved_count` counts considered results; recall is relevant hits / relevant_total.
  Reciprocal rank is `1 / first_relevant_rank` using one-based ranks, or zero if none.
- Compute `DCG@k = sum((2**grade - 1) / log2(rank + 1))` over the considered results.
  Ideal DCG uses the best k grades from **all** judgments for that query, sorted descending.
  nDCG is DCG / ideal DCG. If no positive judgments exist, recall, reciprocal rank and
  nDCG are all zero; that query still contributes to the mean.
- `per_query` is a tuple sorted by query ID. The three aggregate values are arithmetic
  means over every declared query, including missing runs and no-positive queries.
  Use unrounded native Python floats. Do not mutate caller data.

This is macro averaging, not a pooled ratio over all relevant documents. MRR is truncated
at k in this exercise. The explicit zero policy for no-positive queries differs from
evaluation systems that exclude them; report the convention with any real result.

## Edge cases

Missing runs, unsorted query mappings, a document relevant to a different query,
graded relevance, relevant documents outside top-k, no-positive queries, duplicates
beyond the cutoff and invalid IDs/grades.

## Run

```powershell
uv run pytest modules/06_rag/06_rag_evaluation/exercises/retrieval_evaluation -q
```

Done when every declared query has an auditable row and aggregate metrics cannot improve
merely because a failed retrieval run disappears from `results`.
