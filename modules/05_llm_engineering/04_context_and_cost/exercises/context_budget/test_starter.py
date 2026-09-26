"""Check budgets with hand-counted fixtures, including non-character counters."""

import pytest

from roadmap_tools import exercise_call

from .starter import Document, PackedContext, pack_context


def test_reserves_output_and_overhead_at_exact_fit() -> None:
    docs = (Document("a", "1234"), Document("b", "123"), Document("c", "x"))
    result = exercise_call(pack_context, docs, 12, 3, 2, len)
    assert result == PackedContext(docs[:2], ("c",), 9)


def test_skips_oversized_document_and_continues_in_priority_order() -> None:
    docs = (Document("big", "123456"), Document("small", "123"), Document("tiny", "12"))
    result = exercise_call(pack_context, docs, 8, 2, 1, len)
    assert result.selected == docs[1:]
    assert result.dropped_ids == ("big",)
    assert result.input_tokens == 6


def test_uses_injected_counter_not_text_length() -> None:
    docs = (Document("owl", "owl"), Document("eagle", "eagle"), Document("fox", "fox"))
    costs = {"owl": 4, "eagle": 1, "fox": 2}
    seen: list[str] = []

    def count(text: str) -> int:
        seen.append(text)
        return costs[text]

    result = exercise_call(pack_context, docs, 5, 1, 0, count)
    assert result == PackedContext((docs[0],), ("eagle", "fox"), 4)
    assert seen == ["owl", "eagle", "fox"]


def test_empty_and_zero_cost_documents_fit_zero_remainder() -> None:
    docs = (Document("empty", ""), Document("costly", "x"))
    result = exercise_call(pack_context, docs, 4, 3, 1, len)
    assert result == PackedContext((docs[0],), ("costly",), 1)


def test_empty_input_still_accounts_for_overhead() -> None:
    assert exercise_call(pack_context, (), 10, 3, 2, len) == PackedContext((), (), 2)


@pytest.mark.parametrize(
    ("limit", "reserved", "overhead"),
    [(0, 0, 0), (-1, 0, 0), (10, -1, 0), (10, 0, -1), (5, 4, 2)],
)
def test_rejects_impossible_budgets(limit: int, reserved: int, overhead: int) -> None:
    with pytest.raises(ValueError, match=r"budget|limit|reserved|overhead"):
        exercise_call(pack_context, (), limit, reserved, overhead, len)


def test_rejects_negative_counter_result_even_for_dropped_document() -> None:
    with pytest.raises(ValueError, match=r"count|token"):
        exercise_call(pack_context, (Document("a", "x"),), 1, 1, 0, lambda _: -1)


@pytest.mark.parametrize(
    "docs",
    [(Document(" ", "x"),), (Document("a", "x"), Document("a", "y"))],
)
def test_rejects_blank_and_duplicate_identifiers(docs: tuple[Document, ...]) -> None:
    with pytest.raises(ValueError, match=r"identifier|document"):
        exercise_call(pack_context, docs, 10, 1, 0, len)


def test_never_truncates_or_mutates_documents() -> None:
    docs = (Document("fern", " fern\nleaf "), Document("moss", "moss"))
    result = exercise_call(pack_context, docs, 8, 1, 0, len)
    assert result.selected == (Document("moss", "moss"),)
    assert docs == (Document("fern", " fern\nleaf "), Document("moss", "moss"))
