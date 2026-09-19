"""Smoke tests for the standalone Module 01 teaching examples."""

import asyncio
import runpy
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest

MODULE_ROOT = Path(__file__).parents[1]
EXAMPLE_PATHS = [
    MODULE_ROOT / lesson / "example.py"
    for lesson in (
        "00_environment",
        "01_object_model",
        "02_collections",
        "03_functions",
        "04_typing",
        "05_data_modeling",
        "06_exceptions_io",
        "07_iterators_generators",
        "08_decorators",
        "09_testing",
        "10_asyncio",
    )
]


def load_example(path: Path) -> dict[str, Any]:
    """Load an example by path so numbered lesson folders never become imports."""
    return runpy.run_path(str(path))


@pytest.mark.parametrize("path", EXAMPLE_PATHS, ids=lambda path: path.parent.name)
def test_examples_export_and_run_main_without_stderr(
    path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    namespace = load_example(path)
    main = namespace["main"]

    assert callable(main)
    cast(Callable[[], None], main)()
    assert capsys.readouterr().err == ""


def test_object_example_distinguishes_identity_from_equality() -> None:
    namespace = load_example(MODULE_ROOT / "01_object_model" / "example.py")
    compare_ticket_tags = cast(Callable[[], tuple[bool, bool]], namespace["compare_ticket_tags"])

    same_object, same_value = compare_ticket_tags()

    assert same_object is False
    assert same_value is True


def test_generator_example_returns_a_lazy_iterator() -> None:
    namespace = load_example(MODULE_ROOT / "07_iterators_generators" / "example.py")
    stream_log_lines = cast(Callable[[], Iterator[str]], namespace["stream_log_lines"])

    lines = stream_log_lines()

    assert iter(lines) is lines
    assert next(lines) == "INFO document=terms parsed"


def test_decorator_example_preserves_the_wrapped_name() -> None:
    namespace = load_example(MODULE_ROOT / "08_decorators" / "example.py")
    parse_document = cast(Callable[[str], int], namespace["parse_document"])

    assert parse_document.__name__ == "parse_document"


def test_async_example_gather_preserves_request_order() -> None:
    namespace = load_example(MODULE_ROOT / "10_asyncio" / "example.py")
    collect_metadata = cast(Callable[[list[str]], Any], namespace["collect_metadata"])

    result = asyncio.run(collect_metadata(["risk", "compliance", "support"]))

    assert result == ["risk:ready", "compliance:ready", "support:ready"]
