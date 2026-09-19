"""Test-only adapter for student exercise boundaries."""

from collections.abc import Callable
from typing import TypeVar

import pytest

T = TypeVar("T")


def exercise_call(operation: Callable[..., T], /, *args: object, **kwargs: object) -> T:
    """Run an exercise operation, marking only unfinished boundaries as expected incomplete."""
    try:
        return operation(*args, **kwargs)
    except NotImplementedError as exc:
        pytest.xfail(f"Exercise not implemented yet: {exc}")
