"""Smoke tests for the standalone Module 01 teaching examples."""

import asyncio
import re
import runpy
import subprocess
import sys
from collections.abc import Awaitable, Callable, Iterator
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

import pytest

MODULE_ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = MODULE_ROOT.parents[1]
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


def test_decorator_example_reports_elapsed_time_with_an_injected_clock() -> None:
    namespace = load_example(MODULE_ROOT / "08_decorators" / "example.py")
    timed = cast(Callable[..., Any], namespace["timed"])
    readings = iter((10.0, 10.25))
    reports: list[str] = []

    def count_words(text: str) -> int:
        return len(text.split())

    measured_count = cast(
        Callable[[str], int],
        timed(clock=lambda: next(readings), reporter=reports.append)(count_words),
    )

    assert measured_count("terms and conditions") == 3
    assert measured_count.__name__ == "count_words"
    assert reports == ["count_words took 0.250s"]


def test_decorator_example_main_uses_a_deterministic_timing_demo(
    capsys: pytest.CaptureFixture[str],
) -> None:
    namespace = load_example(MODULE_ROOT / "08_decorators" / "example.py")
    main = cast(Callable[[], None], namespace["main"])

    main()

    assert capsys.readouterr().out == "3 words; demo_parse_document took 0.125s\n"


def test_async_example_starts_all_calls_before_controlled_release_and_keeps_input_order() -> None:
    namespace = load_example(MODULE_ROOT / "10_asyncio" / "example.py")
    metadata_fetcher = Callable[[str], Awaitable[str]]
    collect_metadata = cast(
        Callable[[list[str], metadata_fetcher], Awaitable[list[str]]], namespace["collect_metadata"]
    )

    async def run_scenario() -> tuple[list[str], list[str]]:
        topics = ["risk", "compliance", "support"]
        started: set[str] = set()
        completed: list[str] = []
        all_started = asyncio.Event()
        releases = {topic: asyncio.Event() for topic in topics}
        completions = {topic: asyncio.Event() for topic in topics}

        async def fetch(topic: str) -> str:
            started.add(topic)
            if len(started) == len(topics):
                all_started.set()
            await releases[topic].wait()
            completed.append(topic)
            completions[topic].set()
            return f"{topic}:ready"

        gather_task = asyncio.ensure_future(collect_metadata(topics, fetch))
        try:
            await asyncio.wait_for(all_started.wait(), timeout=1.0)
            assert started == set(topics)
            assert gather_task.done() is False

            for topic in ("support", "risk", "compliance"):
                releases[topic].set()
                await completions[topic].wait()

            return await gather_task, completed
        except BaseException:
            gather_task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await gather_task
            raise

    result, completion_order = asyncio.run(run_scenario())

    assert completion_order == ["support", "risk", "compliance"]
    assert result == ["risk:ready", "compliance:ready", "support:ready"]


@pytest.mark.parametrize("example_path", EXAMPLE_PATHS, ids=lambda path: path.parent.name)
def test_lesson_readme_example_commands_resolve_from_repository_root(example_path: Path) -> None:
    readme = example_path.with_name("README.md")
    commands = re.findall(r"`uv run python ([^`\s]+)`", readme.read_text(encoding="utf-8"))

    assert commands
    for command_path in commands:
        assert (REPOSITORY_ROOT / command_path).resolve() == example_path.resolve()


def test_testing_example_runs_real_parameterized_pytest_cases() -> None:
    example_path = MODULE_ROOT / "09_testing" / "example.py"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(example_path), "-q"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed" in result.stdout
