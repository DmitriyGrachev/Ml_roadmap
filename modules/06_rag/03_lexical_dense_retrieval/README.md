# Lexical and dense retrieval

## Goal

The [Russian TF-IDF versus dense-retrieval explanation](theory.md) includes computed
scores from the separate teacher walkthrough and an OOV diagnostic.

Compare exact vocabulary matching with vector similarity and select authorized evidence
before truncating to a candidate budget. Treat retrieval quality as an empirical question.

## Java mental model

A lexical index resembles an inverted lookup structure; a dense index stores learned
numeric representations. Neither replaces metadata filters or an authorization check.
Keep the embedding model/version and vector dimensions in the index schema.

## Python model

`TfidfVectorizer` learns vocabulary and inverse-document-frequency weights from the
indexed corpus, then transforms queries into that same space. Cosine similarity compares
directions. Query and document embeddings must use compatible models and preprocessing.

## Key concepts

- Sparse matching often helps identifiers and exact phrases; vocabulary mismatch can miss synonyms.
- Dense embeddings can capture learned relationships but need a suitable model and evaluation.
- These tiny hand-supplied vectors teach geometry only; they are not pretrained semantic embeddings.
- Exact search is a useful reference. Approximate nearest-neighbor indexes trade recall,
  memory and latency; measure the tradeoff on authorized queries and realistic corpus sizes.
- Filtering after global top-k can discard most results while missing eligible candidates.
  Enforce access before selecting results and recheck before exposing context or cached answers.

References: [TF-IDF API](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html),
[cosine similarity](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html),
[vector ranking](https://learn.microsoft.com/en-us/azure/search/vector-search-ranking), and
[filter placement](https://learn.microsoft.com/en-us/azure/search/vector-search-filters).

## Example

```powershell
uv run python modules/06_rag/03_lexical_dense_retrieval/example.py
```

Inspect lexical similarity for library/garden/trail sentences and an out-of-vocabulary
query. A separate two-vector calculation shows scale invariance without implementing
the exercise's authorized ranking function.

## Exercises

Complete [Authorized vector search](exercises/vector_search/README.md): exact cosine,
explicit roles, zero vectors, dimension checks, finite scores and stable ties.

## Self-check

1. What does an out-of-vocabulary TF-IDF query produce?
2. Why must query and document vectors share an embedding space?
3. What does cosine ignore that a raw dot product retains?
4. How would you measure the quality cost of approximate search?
5. Why can filtering after top-k return too few authorized results?

## Done when

You can distinguish lexical and dense failure modes, reproduce an exact-search baseline,
and select a bounded set of authorized results with deterministic ordering.
