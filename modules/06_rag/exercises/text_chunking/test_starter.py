"""Behavioral contracts for overlapping text chunks."""

from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import TextChunk, chunk_document


@pytest.mark.student_exercise
def test_overlap_partial_tail_stable_ids_and_offsets() -> None:
    assert exercise_call(chunk_document, "guide", "a b c d e f g h", chunk_size=4, overlap=1) == (
        TextChunk("guide:0", "guide", 0, 0, 4, "a b c d"),
        TextChunk("guide:1", "guide", 1, 3, 7, "d e f g"),
        TextChunk("guide:2", "guide", 2, 6, 8, "g h"),
    )


@pytest.mark.student_exercise
def test_exact_last_window_does_not_emit_a_redundant_overlap_tail() -> None:
    assert exercise_call(chunk_document, "doc", "a b c d e f", chunk_size=4, overlap=2) == (
        TextChunk("doc:0", "doc", 0, 0, 4, "a b c d"),
        TextChunk("doc:1", "doc", 1, 2, 6, "c d e f"),
    )


@pytest.mark.student_exercise
def test_whitespace_is_normalized_but_punctuation_and_unicode_are_preserved() -> None:
    assert exercise_call(
        chunk_document, "d", "  café!\n雪\tgreen\r\n", chunk_size=5, overlap=0
    ) == (TextChunk("d:0", "d", 0, 0, 3, "café! 雪 green"),)


@pytest.mark.student_exercise
def test_zero_overlap_size_one_and_high_overlap() -> None:
    assert exercise_call(chunk_document, "d", "a b", chunk_size=1, overlap=0) == (
        TextChunk("d:0", "d", 0, 0, 1, "a"),
        TextChunk("d:1", "d", 1, 1, 2, "b"),
    )
    chunks = exercise_call(chunk_document, "d", "a b c d e", chunk_size=3, overlap=2)
    assert [(chunk.start_word, chunk.end_word) for chunk in chunks] == [(0, 3), (1, 4), (2, 5)]


@pytest.mark.student_exercise
@pytest.mark.parametrize("text", ["", " \t\n"])
def test_empty_document(text: str) -> None:
    assert exercise_call(chunk_document, "empty", text) == ()


@pytest.mark.student_exercise
def test_repeated_calls_and_document_ids_remain_independent() -> None:
    source = "one two three"
    first = exercise_call(chunk_document, " A ", source, chunk_size=2, overlap=0)
    assert first == exercise_call(chunk_document, " A ", source, chunk_size=2, overlap=0)
    other = exercise_call(chunk_document, "B", source, chunk_size=2, overlap=0)
    assert {chunk.id for chunk in first}.isdisjoint(chunk.id for chunk in other)
    assert first[0].id == " A :0"
    assert source == "one two three"


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [
        (0, 0),
        (-1, 0),
        (True, 0),
        (2.5, 0),
        (3, -1),
        (3, 3),
        (3, 4),
        (3, True),
        (3, 0.5),
    ],
)
def test_invalid_sizes_even_for_empty_text(chunk_size: object, overlap: object) -> None:
    with pytest.raises(ValueError, match=r"chunk_size|overlap"):
        exercise_call(chunk_document, "d", "", chunk_size=chunk_size, overlap=overlap)


@pytest.mark.parametrize("document_id", ["", "  ", None])
def test_invalid_document_id(document_id: object) -> None:
    with pytest.raises(ValueError, match="document_id"):
        exercise_call(chunk_document, document_id, "words")


def test_invalid_text() -> None:
    with pytest.raises(ValueError, match="text"):
        exercise_call(chunk_document, "d", cast(str, None))
