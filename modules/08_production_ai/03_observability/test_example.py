"""Trace relationships are not inferred by summing concurrent operations."""

import pytest

from .example import main, museum_trace


def test_child_spans_overlap_within_the_root() -> None:
    root, *children = museum_trace()
    assert root.duration_ms == 150
    assert sum(child.duration_ms for child in children) == 175
    assert all(root.start_ms <= child.start_ms < child.end_ms <= root.end_ms for child in children)
    assert children[0].start_ms == children[1].start_ms


def test_example_is_repeatable(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    first = capsys.readouterr().out
    main()
    assert capsys.readouterr().out == first
