# Ingestion, chunking and index lifecycle

## Goal

Read the [Russian theory on normalization, paragraph chunks and revisions](theory.md)
before using the existing update-plan example.

Convert changing documents into traceable searchable units without leaving stale chunks
behind. Retain the source, revision and extraction/chunking configuration for every unit.

## Java mental model

An index is a derived read model, similar to a materialized projection. A source update
can replace many indexed rows. Idempotent ingestion, version checks and deletion events
matter as much as the initial insert.

## Python model

Extract text with a documented normalization policy, partition it into chunks, record
offsets, and index those chunks with metadata. Use a content digest to detect changes,
then publish a complete new source revision and retire every old chunk for that source.
The example plans updates; it deliberately does not implement a storage engine.

## Key concepts

- Smaller chunks reduce irrelevant context but can separate a rule from its exception.
- Overlap preserves neighboring context while increasing duplicate retrieval and index size.
- The existing exercise uses whitespace-word offsets, not model-token or byte offsets.
- A stable chunk identity is stable within a declared source revision and chunking policy.
  `document_id:index` alone can refer to different text after an edit; carry revision metadata.
- Hash extraction policy and source content; record embedding model/version separately.
- Shortening a source must remove its old tail chunks. Deletion tombstones also invalidate
  answer caches and downstream copies according to the application's retention policy.

References: [Python hashlib](https://docs.python.org/3/library/hashlib.html) and
[RAG indexing considerations](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview).

## Example

```powershell
uv run python modules/06_rag/02_ingestion_chunking/example.py
```

Compare two tiny garden-document snapshots. The update plan distinguishes unchanged
sources, replacements/new sources and deletion tombstones without writing any files.

## Exercises

Complete the unchanged [Chunk documents with overlap](../exercises/text_chunking/README.md)
exercise. Its earlier standalone description remains valid: it needs no embedding model
or RAG service. Explain how revision metadata would wrap those existing chunk IDs.

## Self-check

1. What must happen when an updated document produces fewer chunks?
2. Why can changing a parser require reindexing unchanged source bytes?
3. Which offset coordinate system does the chunking exercise use?
4. How does overlap affect index size and duplicate evidence?
5. What must be invalidated when an accessible source is deleted?

## Done when

Your chunks preserve the exercise's offsets and IDs, and you can explain an idempotent
update plan that replaces stale revisions and removes deleted sources.
