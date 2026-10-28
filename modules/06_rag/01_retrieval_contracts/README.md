# Retrieval contracts and provenance

## Goal

Start with the [Russian theory and G-01 provenance walkthrough](theory.md); it connects
the Module 05 guide to the complete retrieval chain.

Define what the system can answer, who can access each source and what evidence every
retrieved passage must carry. A library-hours answer should identify the relevant
branch and current schedule, not merely return a plausible sentence.

## Java mental model

Model the retriever as a service returning evidence DTOs: chunk ID, source ID, revision,
text and score. Authorization belongs to the application boundary; a prompt is not an
access-control implementation. Keep presentation URLs distinct from stable source IDs.

## Python model

Use frozen records and an explicit corpus snapshot. Carry query ID, requester roles,
retrieval settings and evidence identifiers through the request. A generated answer
and the evidence supplied to the model are separate artifacts for evaluation.

## Key concepts

- RAG retrieves external material at inference time; it does not inherently update model weights.
- Specify supported question types, freshness limits and what requires abstention.
- Retrieval similarity is not a calibrated probability that an answer is correct.
- Source text is untrusted data even when the requester may read it. Embedded commands
  have no authority to change tool permissions or application instructions.
- Provenance needs a source revision and extraction policy, not just a human-readable title.

References: [original RAG research](https://arxiv.org/abs/2005.11401) and
[RAG architecture overview](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview).

## Example

```powershell
uv run python modules/06_rag/01_retrieval_contracts/example.py
```

Inspect a JSON evidence envelope for a library schedule. It carries provenance and
clearly labels the snippet as data; it neither contacts a model nor grants permissions.

## Exercises

Write a contract for trail-access questions: source owner, revision, freshness,
authorized audience and abstention condition. Carry these constraints into
[authorized vector search](../03_lexical_dense_retrieval/exercises/vector_search/README.md).

## Self-check

1. Which part of a RAG system changes when a library updates its hours?
2. Why is a source title insufficient as an identifier?
3. Who enforces access to retrieved text?
4. Why does high similarity not establish truth?
5. What evidence must be logged to investigate an unsupported answer?

## Done when

You can draw a boundary between user intent, authorized source data and generated
claims, and describe the metadata needed to trace one answer to a source snapshot.
