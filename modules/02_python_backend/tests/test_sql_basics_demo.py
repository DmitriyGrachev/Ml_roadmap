"""Check teaching SQL against hand-counted rows; SQLite is not PostgreSQL evidence."""

from importlib import import_module
from typing import Any


def demo() -> Any:
    return import_module("modules.02_python_backend.07_postgresql.sql_basics_demo")


def test_null_filter_and_stable_sort() -> None:
    result = demo().run_demo()
    assert result["filtered"] == [(3, "south", 12), (4, "south", 12), (1, "north", 8)]
    assert result["null_equals"] == []
    assert result["null_is"] == [(2,)]


def test_left_join_counts_unmatched_group_and_null_values() -> None:
    assert demo().run_demo()["grouped"] == [
        ("north", 2, 1, 8),
        ("south", 2, 2, 24),
        ("west", 0, 0, None),
    ]
    assert demo().run_demo()["having"] == [("south", 12.0)]


def test_many_to_many_join_multiplies_rows() -> None:
    assert demo().run_demo()["joined"] == [
        (1, "indoor"),
        (1, "quiet"),
        (2, "indoor"),
        (2, "quiet"),
        (3, "outdoor"),
        (4, "outdoor"),
    ]


def test_window_keeps_rows_and_distinguishes_ties() -> None:
    assert demo().run_demo()["windowed"] == [
        (1, "north", 8, 1, 1),
        (2, "north", None, 2, 2),
        (3, "south", 12, 1, 1),
        (4, "south", 12, 2, 1),
    ]


def test_repeated_runs_are_fresh_in_memory() -> None:
    first = demo().run_demo()
    first["filtered"].clear()
    assert len(demo().run_demo()["filtered"]) == 3
