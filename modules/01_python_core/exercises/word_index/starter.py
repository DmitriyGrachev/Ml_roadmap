"""Student boundary for an inverted index over small text documents."""

from collections.abc import Mapping


def build_word_index(documents: Mapping[str, str]) -> dict[str, tuple[str, ...]]:
    """Map each lowercase ASCII word to sorted, unique document IDs."""
    # TODO: validate documents, tokenize, collect membership, and order the result.
    raise NotImplementedError("build a word index")
