# Hybrid retrieval and reranking

## Goal

The [Russian fusion and reranking theory](theory.md) gives a small manual RRF
calculation without implementing the student exercise.

Combine complementary candidate lists without confusing incomparable scores, then
rerank an authorized shortlist while tracking latency and candidate coverage.

## Java mental model

Think of fan-out to two search adapters followed by a deterministic merge and a more
expensive ranking stage. A merge function cannot repair a document absent from every
candidate list, just as a downstream sort cannot restore a dropped database row.

## Python model

Lexical and vector score scales need not match. Reciprocal rank fusion (RRF) combines
positions using `weight / (rank_constant + rank)` with ranks starting at one. A reranker
can then score query/document pairs on a bounded shortlist; its score remains a ranking
signal, not proof of truth or authorization.

## Key concepts

- Fuse unique document IDs while preserving source/chunk identity for later citations.
- A larger rank constant flattens differences between early ranks; tune on development queries.
- Cross-encoder rerankers jointly inspect query and document and usually cost more per pair
  than retrieving precomputed embeddings. They cannot recover missing candidates.
- Apply authorization independently in each retrieval branch; recompute authorized ranks.
  Recheck access before context assembly, including after cache hits or permission changes.
- Candidate count, rerank count and context count are distinct budgets.

Reference: [RRF and ranking stages](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking).

## Example

```powershell
uv run python modules/06_rag/04_hybrid_reranking/example.py
```

A synthetic shortlist is reordered using fixed illustrative reranker scores. This
demonstrates the candidate ceiling, not a trained reranker or an RRF implementation.

## Exercises

Complete [Reciprocal rank fusion](exercises/reciprocal_rank_fusion/README.md), including
weights, duplicate detection, one-based ranks, zero-weight branches and stable ties.

## Self-check

1. Why is directly adding TF-IDF and cosine scores questionable?
2. What does the RRF rank constant control?
3. Can a reranker return a document that never entered its shortlist?
4. Where must permissions be checked when two retrieval branches are combined?
5. Which three candidate/context budgets should be measured separately?

## Done when

You can explain and test deterministic rank fusion, distinguish it from reranking,
and identify both authorization and recall boundaries in the combined pipeline.
