# Module 06 — Retrieval-Augmented Generation

## Goal

Build a measurable retrieval-augmented generation workflow: ingest versioned sources,
retrieve authorized evidence, preserve provenance, and evaluate retrieval separately
from answer behavior. Examples use a small local library, garden and trail corpus.

## Prerequisites

Complete the implemented [data foundations module](../03_data_foundations/README.md)
and the implemented [LLM engineering module](../05_llm_engineering/README.md).
Familiarity with APIs, persistence boundaries, typed records and tests is expected.
All commands run offline after environment setup, using existing dependencies only.

## Java mental model

Treat retrieval as a versioned search service with an authorization boundary and a
typed response contract. Adding retrieved text to a prompt does not make that text
trusted instructions or guarantee that an answer follows from it.

## Python model

Use immutable records, explicit IDs and deterministic ranking. Separate ingestion,
candidate retrieval, fusion/reranking, context assembly and evaluation. Tiny supplied
vectors demonstrate geometry, not pretrained semantics or real retrieval quality.

## Key concepts

| Lesson | Practice |
| --- | --- |
| [01 Retrieval contracts and provenance](01_retrieval_contracts/README.md) | Write a query and evidence contract |
| [02 Ingestion, chunking and index lifecycle](02_ingestion_chunking/README.md) | [Existing text chunking exercise](exercises/text_chunking/README.md) |
| [03 Lexical and dense retrieval](03_lexical_dense_retrieval/README.md) | [Authorized vector search](03_lexical_dense_retrieval/exercises/vector_search/README.md) |
| [04 Hybrid retrieval and reranking](04_hybrid_reranking/README.md) | [Reciprocal rank fusion](04_hybrid_reranking/exercises/reciprocal_rank_fusion/README.md) |
| [05 Grounded answers and citation checks](05_grounded_answers/README.md) | [Evidence citation validation](05_grounded_answers/exercises/citation_validation/README.md) |
| [06 Retrieval and answer evaluation](06_rag_evaluation/README.md) | [Retrieval evaluation by query](06_rag_evaluation/exercises/retrieval_evaluation/README.md) |

## Example

Run from the repository root:

```powershell
uv run python modules/06_rag/03_lexical_dense_retrieval/example.py
uv run pytest modules/06_rag -q
uv run mypy -p modules.06_rag
```

Each lesson contains a deterministic runnable example and behavioral checks. No vector
database, embedding download, provider service or API key is required.

## Exercises

Complete eight Medium exercises: the five core tasks in the lesson table and three
additional tasks below, taking 45–75 minutes each. Their READMEs define exact validation
and ranking policies.
Unimplemented boundaries remain expected-incomplete; incorrect attempts fail normally.
The existing chunking contract uses document/index IDs within a versioned snapshot;
the ingestion lesson explains the extra revision metadata needed across updates.

| Lesson connection | Additional practice |
| --- | --- |
| Ingestion and index lifecycle | [Plan a library index refresh](exercises/index_sync/README.md) |
| Retrieval and context assembly | [Diversify retrieved museum evidence](exercises/context_diversity/README.md) |
| Retrieval evaluation | [Guard query-level retrieval regressions](exercises/retrieval_regression/README.md) |

## Self-check

1. Which source snapshot and permissions produced a retrieved passage?
2. What happens to indexed chunks when a source is deleted or shortened?
3. Why must authorization precede candidate selection and downstream context assembly?
4. What can a successful quote check establish, and what can it not establish?
5. How will you separate retrieval misses from unsupported generated answers?

## Done when

You can run the six examples, complete eight exercises, and explain a RAG result through
its source version, ranking decisions, access policy, evidence and held-out evaluation.
