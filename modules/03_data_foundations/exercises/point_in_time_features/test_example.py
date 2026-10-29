"""The worked window excludes the query instant and poisoned future."""

from .example import run_example


def test_fixed_window_has_inclusive_left_and_exclusive_right_edge() -> None:
    assert run_example() == {"event_ids": ["left", "inside"], "count": 2, "sum": 12.0, "mean": 6.0}
