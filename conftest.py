"""Keep template publication policy separate from a learner's working suite."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--maintainer",
        action="store_true",
        default=False,
        help="also run policy checks requiring distributed starters to remain unsolved",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--maintainer"):
        return
    selected = []
    deselected = []
    for item in items:
        (deselected if item.get_closest_marker("maintainer_only") else selected).append(item)
    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)
