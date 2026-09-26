"""Deterministic assembly of a single museum-answer stream."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import StreamEvent, StreamResult, assemble_stream

pytestmark = pytest.mark.student_exercise


def test_reorders_frames_by_sequence_and_preserves_exact_delta_text() -> None:
    events = (
        StreamEvent("s", 2, "done"),
        StreamEvent("s", 1, "delta", " café!"),
        StreamEvent("s", 0, "delta", "Museum"),
    )
    assert exercise_call(assemble_stream, "s", events) == StreamResult(
        "Museum café!", "complete", None
    )


def test_incomplete_and_empty_streams() -> None:
    assert exercise_call(assemble_stream, "s", ()) == StreamResult("", "incomplete", None)
    assert exercise_call(
        assemble_stream, "s", (StreamEvent("s", 0, "delta", "A"),)
    ) == StreamResult("A", "incomplete", None)


def test_error_preserves_partial_text_and_error_message() -> None:
    assert exercise_call(
        assemble_stream,
        "s",
        (StreamEvent("s", 0, "delta", "Partial "), StreamEvent("s", 1, "error", "unavailable")),
    ) == StreamResult("Partial ", "error", "unavailable")


def test_terminal_only_and_empty_delta_are_valid() -> None:
    assert exercise_call(assemble_stream, "s", (StreamEvent("s", 0, "done"),)) == StreamResult(
        "", "complete", None
    )
    assert exercise_call(
        assemble_stream, "s", (StreamEvent("s", 0, "delta", ""), StreamEvent("s", 1, "done"))
    ) == StreamResult("", "complete", None)


@pytest.mark.parametrize(
    "events",
    [
        (StreamEvent("s", 1, "delta", "gap"),),
        (StreamEvent("s", 0, "delta", "A"), StreamEvent("s", 2, "done")),
        (StreamEvent("s", 0, "delta", "A"), StreamEvent("s", 0, "delta", "A")),
        (StreamEvent("s", 0, "done"), StreamEvent("s", 1, "delta", "late")),
        (StreamEvent("s", 0, "error", "oops"), StreamEvent("s", 1, "done")),
        (StreamEvent("other", 0, "delta", "A"),),
        (StreamEvent("s", -1, "delta", "A"),),
        (StreamEvent("s", 0, "done", "unexpected"),),
        (StreamEvent("s", 0, "error", " "),),
    ],
)
def test_invalid_streams_raise_instead_of_returning_partial_success(
    events: tuple[StreamEvent, ...],
) -> None:
    with pytest.raises(ValueError):
        exercise_call(assemble_stream, "s", events)


def test_blank_stream_id_is_invalid_even_for_no_events() -> None:
    with pytest.raises(ValueError):
        exercise_call(assemble_stream, " ", ())
