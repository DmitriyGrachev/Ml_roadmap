# Chunk documents with overlap

Difficulty: Medium

## Goal and prerequisites

Build deterministic chunks that retain source offsets for a future retrieval
pipeline. Prerequisites: Python sequences, immutable dataclasses, validation,
and tests. This standalone exercise does not require the planned RAG lessons,
an embedding model, network access, or a vector database. Estimated time: 45–60 minutes.

## Requirements

- `document_id` must be a nonblank string; preserve its exact value, including any
  outer whitespace, in metadata and IDs. `text` must be a string. Invalid arguments
  raise `ValueError` even when the text is empty.
- `chunk_size` must be a positive integer; `overlap` must be an integer with
  `0 <= overlap < chunk_size`. Reject booleans for both integer arguments.
- Words are defined by `text.split()` (all whitespace); preserve word spelling,
  punctuation, and Unicode. Join each chunk's words with one ASCII space.
- The first chunk starts at word 0 and contains at most `chunk_size` words. Each
  subsequent chunk starts `chunk_size - overlap` words after the previous start.
  **Stop as soon as a chunk reaches the document's end.** Do not emit an extra
  chunk containing only a previously covered overlap tail.
- Return a tuple of frozen `TextChunk` values in source order. Record zero-based
  `index`, inclusive `start_word`, exclusive `end_word`, and the original document
  ID. A chunk ID is exactly `f"{document_id}:{index}"`.
- Blank text returns `()`. Short documents return one chunk. Repeated calls have
  equal results; IDs and indices do not depend on calls for other documents.

These word offsets are a learning contract, not tokenizer offsets for any model.

## Example

```python
chunk_document("guide", "a b c d e f", chunk_size=4, overlap=2)
# (
#   TextChunk("guide:0", "guide", 0, 0, 4, "a b c d"),
#   TextChunk("guide:1", "guide", 1, 2, 6, "c d e f"),
# )
```

## TODO boundary

Implement `chunk_document` in `starter.py`. Validation and the immutable result
type are provided. Window construction, stopping behavior, and metadata are TODOs.

## Run

```powershell
uv run pytest modules/06_rag/exercises/text_chunking -q -rx
```

The unfinished boundary produces expected-incomplete (`xfail`) tests. Completion
means all behavioral tests pass without expected-incomplete results.
