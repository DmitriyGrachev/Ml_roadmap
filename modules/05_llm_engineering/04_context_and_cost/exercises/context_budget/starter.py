"""Pack ordered nature-guide excerpts using an injected budget counter."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    identifier: str
    text: str


@dataclass(frozen=True)
class PackedContext:
    selected: tuple[Document, ...]
    dropped_ids: tuple[str, ...]
    input_tokens: int


def pack_context(
    documents: tuple[Document, ...],
    context_limit: int,
    reserved_output: int,
    overhead: int,
    count_tokens: Callable[[str], int],
) -> PackedContext:
    """Pack whole documents greedily in order; see README.md for budget semantics."""
    raise NotImplementedError("Implement whole-document context packing")
