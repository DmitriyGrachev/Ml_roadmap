"""Acceptance tests for lazy NDJSON transaction streaming."""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

from roadmap_tools import exercise_call

from .starter import stream_transactions


class TrackingLines(Iterator[str]):
    def __init__(self, lines: list[str]) -> None:
        self._lines = iter(lines)
        self.read_count = 0

    def __iter__(self) -> TrackingLines:
        return self

    def __next__(self) -> str:
        line = next(self._lines)
        self.read_count += 1
        return line


def test_stream_creation_does_not_read_the_source() -> None:
    source = TrackingLines(['{"id":"txn-1"}\n'])

    rows = stream_transactions(source)

    assert source.read_count == 0
    assert iter(rows) is rows


@pytest.mark.student_exercise
def test_each_next_reads_only_one_ndjson_record() -> None:
    source = TrackingLines(
        [
            '{"id":"txn-1","status":"posted"}\n',
            '{"id":"txn-2","status":"reversed"}\n',
        ]
    )
    rows = stream_transactions(source)

    assert exercise_call(next, rows) == {"id": "txn-1", "status": "posted"}
    assert source.read_count == 1
    assert exercise_call(next, rows) == {"id": "txn-2", "status": "reversed"}
    assert source.read_count == 2
    with pytest.raises(StopIteration):
        exercise_call(next, rows)


@pytest.mark.student_exercise
def test_empty_stream_is_immediately_exhausted() -> None:
    assert exercise_call(list, stream_transactions(iter(()))) == []


@pytest.mark.student_exercise
def test_invalid_json_propagates_a_clear_decoder_error() -> None:
    rows = stream_transactions(["not-json\n"])

    with pytest.raises(json.JSONDecodeError):
        exercise_call(next, rows)


@pytest.mark.student_exercise
def test_non_object_json_row_is_rejected() -> None:
    rows = stream_transactions(['["txn-1"]\n'])

    with pytest.raises(ValueError, match="object"):
        exercise_call(next, rows)
