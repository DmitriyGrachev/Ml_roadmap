"""Student boundary for deterministic overlapping document chunks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """One chunk with a stable ID and half-open word offsets."""

    id: str
    document_id: str
    index: int
    start_word: int
    end_word: int
    text: str


def chunk_document(
    document_id: str,
    text: str,
    *,
    chunk_size: int = 100,
    overlap: int = 20,
) -> tuple[TextChunk, ...]:
    """Split whitespace-delimited words using the documented overlap contract."""
    if not isinstance(document_id, str) or not document_id.strip():
        raise ValueError("document_id must be a nonblank string")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if type(overlap) is not int or not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be an integer from zero to chunk_size - 1")
    # TODO: produce word windows, normalized chunk text, IDs, and source offsets.
    raise NotImplementedError("chunk document with overlap")
