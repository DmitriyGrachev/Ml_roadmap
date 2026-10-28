"""Small teacher contracts for testing and decomposition."""

import pytest


def preview(text: str, limit: int) -> str:
    """Return at most limit characters; reject non-string text and invalid limits."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if type(limit) is not int or limit < 0:
        raise ValueError("limit must be a nonnegative integer, not bool")
    return text[:limit]


def paragraphs(text: str) -> tuple[str, ...]:
    """Split exactly on blank lines; remove whitespace-only chunks."""
    return tuple(chunk.strip() for chunk in text.split("\n\n") if chunk.strip())


def count_words(paragraph: str) -> int:
    """Whitespace-delimited words, not a natural-language tokenizer."""
    return len(paragraph.split())


def paragraph_word_counts(text: str) -> tuple[int, ...]:
    """Compose two local transformations without retaining per-call state."""
    return tuple(count_words(paragraph) for paragraph in paragraphs(text))


@pytest.mark.parametrize(
    ("text", "limit", "expected"),
    [
        ("atlas", 3, "atl"),
        ("", 4, ""),
        ("atlas", 0, ""),
        ("atlas", 5, "atlas"),
        ("atlas", 6, "atlas"),
    ],
)
def test_preview_examples(text: str, limit: int, expected: str) -> None:
    assert preview(text, limit) == expected


@pytest.mark.parametrize("limit", [-1, True, 1.5])
def test_preview_rejects_invalid_limit(limit: object) -> None:
    with pytest.raises(ValueError, match="limit"):
        # Deliberately exercise runtime validation beyond the static type contract.
        preview("atlas", limit)  # type: ignore[arg-type]


def test_preview_rejects_non_string_text() -> None:
    with pytest.raises(ValueError, match="text"):
        preview(None, 3)  # type: ignore[arg-type]


def main() -> None:
    for text, limit in [("atlas", 3), ("", 4), ("atlas", 0)]:
        print(f"preview({text!r}, {limit}) = {preview(text, limit)!r}")
    document = "red blue\n\ngreen\nleaf\n\n  "
    print(f"paragraphs: {paragraphs(document)!r}")
    print(f"word counts: {paragraph_word_counts(document)!r}")


if __name__ == "__main__":
    main()
