"""An index records document membership, not word frequency."""

from typing import cast

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import build_word_index

pytestmark = pytest.mark.student_exercise


def test_normalizes_ascii_words_and_sorts_keys_and_document_ids() -> None:
    result = exercise_call(build_word_index, {"z": "Rain, SUN!", "a": "sun rain-cloud"})
    assert result == {"cloud": ("a",), "rain": ("a", "z"), "sun": ("a", "z")}
    assert list(result) == ["cloud", "rain", "sun"]


def test_repeated_words_contribute_one_document_id() -> None:
    assert exercise_call(build_word_index, {"b": "Bird bird BIRD"}) == {"bird": ("b",)}


def test_non_ascii_letters_are_delimiters() -> None:
    assert exercise_call(build_word_index, {"d": "café naïve"}) == {
        "caf": ("d",),
        "na": ("d",),
        "ve": ("d",),
    }


def test_digits_underscores_and_apostrophes_separate_words() -> None:
    assert exercise_call(build_word_index, {"d": "room42_blue isn't"}) == {
        "blue": ("d",),
        "isn": ("d",),
        "room": ("d",),
        "t": ("d",),
    }


@pytest.mark.parametrize("documents", [{}, {"a": ""}, {"a": "123 ...\t"}])
def test_documents_without_words(documents: dict[str, str]) -> None:
    assert exercise_call(build_word_index, documents) == {}


def test_input_is_unchanged_and_results_are_independent() -> None:
    documents = {"b": "oak", "a": "Oak elm"}
    before = documents.copy()
    first = exercise_call(build_word_index, documents)
    first.clear()
    assert exercise_call(build_word_index, documents) == {"elm": ("a",), "oak": ("a", "b")}
    assert documents == before


@pytest.mark.parametrize("key", ["", "  ", " a ", 3])
def test_invalid_document_ids(key: object) -> None:
    with pytest.raises(ValueError, match="document"):
        exercise_call(build_word_index, {cast(str, key): "oak"})


def test_non_string_text_is_rejected() -> None:
    with pytest.raises(ValueError, match="document"):
        exercise_call(build_word_index, {"a": cast(str, None)})
