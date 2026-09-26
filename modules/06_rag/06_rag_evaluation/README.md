# Retrieval and answer evaluation

## Goal

Measure whether retrieval finds relevant evidence separately from whether the final
answer is supported, useful and appropriately abstaining. Keep every evaluation query
in the denominator, including queries whose retrieval failed.

## Java mental model

Evaluate the search service and answer service independently, then exercise the entire
request path. An integration failure can arise from indexing, authorization, retrieval,
context selection or generation; one aggregate success rate cannot locate the defect.

## Python model

Join ranked results to relevance judgments by query ID. Use recall@k for evidence
coverage, reciprocal rank for the first relevant result and nDCG for graded ranked
relevance. Record corpus snapshot, query split, relevance policy and retrieval settings.

## Key concepts

- Relevance is query-specific; the same document can help one question and fail another.
- Missing result rows are failed retrievals, not permission to drop evaluation queries.
- Judgment sets are often incomplete. This exercise treats unjudged documents as grade zero;
  report that convention and revisit it when human judgments expand.
- Evaluate answer support, citation integrity, useful abstention and task completion separately.
- Tune chunk size, fusion weights, retrieval k, prompts and thresholds on development queries.
  Keep final queries and near-duplicate source/question families out of tuning; freeze the corpus snapshot.
- Slice by question type, source age, language and access role. Tiny slices remain uncertain.

References: [ranked retrieval evaluation](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html)
and [nDCG API conventions](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html).
The exercise explicitly uses exponential gains; libraries may accept already-transformed gains.

## Example

```powershell
uv run python modules/06_rag/06_rag_evaluation/example.py
```

Classify four manually reviewed garden questions by failure stage. This separates
retrieval coverage from answer support without implementing the ranking-metrics exercise.

## Exercises

Complete [Retrieval evaluation by query](exercises/retrieval_evaluation/README.md).
Then write an answer-support rubric with examples of a supported answer, an unsupported
claim despite good retrieval, and a correct abstention when the source lacks the answer.

## Self-check

1. Why can the same document have different relevance grades for different queries?
2. What happens if a missing retrieval run is omitted from the mean?
3. How do recall@k, reciprocal rank and nDCG reward different rankings?
4. Which RAG configuration choices can leak information from a final query set?
5. Why can high retrieval recall coexist with unsupported answers?

## Done when

You can compute query-aligned metrics over the complete evaluation set and separately
diagnose source, retrieval, context and answer failures using a frozen holdout.
