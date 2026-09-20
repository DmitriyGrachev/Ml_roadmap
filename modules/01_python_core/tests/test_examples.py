"""Smoke tests for the standalone Module 01 teaching examples."""

import ast
import asyncio
import inspect
import io
import logging
import re
import runpy
import subprocess
import sys
from collections.abc import Callable, Iterator
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


def test_typing_example_uses_a_data_protocol_and_normalizes_values() -> None:
    path = MODULE_ROOT / "04_typing" / "example.py"
    namespace = load_example(path)
    normalize_labels = cast(Callable[[object], tuple[str, ...]], namespace["normalize_labels"])

    class LabelsOnly:
        labels = (" Billing ", "urgent", "billing", "")

    assert normalize_labels(LabelsOnly()) == ("billing", "urgent")

    tree = ast.parse(path.read_text(encoding="utf-8"))
    protocol_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases)
    )
    protocol_members = [node for node in protocol_node.body if isinstance(node, ast.FunctionDef)]

    assert protocol_members
    assert all(
        any(
            isinstance(decorator, ast.Name) and decorator.id == "property"
            for decorator in node.decorator_list
        )
        for node in protocol_members
    )


def test_exception_example_reads_and_validates_json_without_an_atomic_export_template(
    tmp_path: Path,
) -> None:
    path = MODULE_ROOT / "06_exceptions_io" / "example.py"
    source = path.read_text(encoding="utf-8")
    namespace = load_example(path)
    load_summary = cast(Callable[[Path], dict[str, str]], namespace["load_summary"])
    invalid_status_error = cast(type[Exception], namespace["InvalidSummaryStatusError"])
    summary = tmp_path / "summary.json"
    summary.write_text('{"document":"terms","status":"ready"}', encoding="utf-8")

    assert load_summary(summary) == {"document": "terms", "status": "ready"}

    summary.write_text('{"document":"terms","status":"pending"}', encoding="utf-8")
    with pytest.raises(invalid_status_error, match="unsupported summary status: pending"):
        load_summary(summary)

    tree = ast.parse(source)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    json_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
    }

    assert "load" in json_calls
    assert json_calls.isdisjoint({"dump", "dumps"})
    assert called_attributes.isdisjoint({"replace", "with_suffix"})


def test_generator_example_returns_a_lazy_iterator() -> None:
    namespace = load_example(MODULE_ROOT / "07_iterators_generators" / "example.py")
    stream_log_lines = cast(Callable[[], Iterator[str]], namespace["stream_log_lines"])

    lines = stream_log_lines()

    assert iter(lines) is lines
    assert next(lines) == "INFO document=terms parsed"


def test_decorator_example_logs_calls_and_preserves_the_wrapped_function() -> None:
    namespace = load_example(MODULE_ROOT / "08_decorators" / "example.py")
    log_calls = cast(Callable[..., Any], namespace["log_calls"])
    messages = io.StringIO()
    logger = logging.Logger("decorator-contract", level=logging.INFO)
    logger.addHandler(logging.StreamHandler(messages))

    def count_terms(query: str) -> int:
        """Count normalized search terms."""

        return len(query.split())

    logged_count = cast(
        Callable[[str], int],
        log_calls(logger=logger)(count_terms),
    )

    assert logged_count("safe payment search") == 3
    assert cast(Any, logged_count).__wrapped__ is count_terms
    assert inspect.signature(logged_count) == inspect.signature(count_terms)
    assert logged_count.__doc__ == count_terms.__doc__
    assert messages.getvalue().splitlines() == [
        "starting count_terms",
        "finished count_terms",
    ]


def test_decorator_example_main_uses_deterministic_logging(
    capsys: pytest.CaptureFixture[str],
) -> None:
    namespace = load_example(MODULE_ROOT / "08_decorators" / "example.py")
    main = cast(Callable[[], None], namespace["main"])

    main()

    assert capsys.readouterr().out == (
        "starting normalize_labels\nfinished normalize_labels\nbilling, urgent\n"
    )


def test_async_example_starts_fixed_heterogeneous_operations_before_release() -> None:
    namespace = load_example(MODULE_ROOT / "10_asyncio" / "example.py")
    build_study_dashboard = namespace["build_study_dashboard"]
    study_dashboard = namespace["StudyDashboard"]

    async def run_scenario() -> Any:
        started: set[str] = set()
        all_started = asyncio.Event()
        release = asyncio.Event()

        async def load_course_title() -> str:
            started.add("title")
            if len(started) == 2:
                all_started.set()
            await release.wait()
            return "Python core"

        async def count_completed_lessons() -> int:
            started.add("count")
            if len(started) == 2:
                all_started.set()
            await release.wait()
            return 4

        function_globals = build_study_dashboard.__globals__
        original_title_loader = function_globals["load_course_title"]
        original_count_loader = function_globals["count_completed_lessons"]
        function_globals["load_course_title"] = load_course_title
        function_globals["count_completed_lessons"] = count_completed_lessons
        gather_task = asyncio.create_task(build_study_dashboard())
        try:
            await asyncio.wait_for(all_started.wait(), timeout=1.0)
            assert started == {"title", "count"}
            assert gather_task.done() is False
            release.set()
            return await asyncio.wait_for(gather_task, timeout=1.0)
        except BaseException:
            gather_task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await gather_task
            raise
        finally:
            function_globals["load_course_title"] = original_title_loader
            function_globals["count_completed_lessons"] = original_count_loader

    result = asyncio.run(run_scenario())

    assert result == study_dashboard(course_title="Python core", completed_lessons=4)


def test_async_example_is_not_a_generic_sequence_fanout_template() -> None:
    path = MODULE_ROOT / "10_asyncio" / "example.py"
    source = path.read_text(encoding="utf-8")
    namespace = load_example(path)
    build_study_dashboard = namespace["build_study_dashboard"]
    study_dashboard = namespace["StudyDashboard"]
    tree = ast.parse(source)
    build_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "build_study_dashboard"
    )
    gather_calls = [
        node
        for node in ast.walk(build_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "asyncio"
        and node.func.attr == "gather"
    ]

    assert "collect_metadata" not in namespace
    assert list(inspect.signature(build_study_dashboard).parameters) == []
    assert inspect.signature(build_study_dashboard).return_annotation is study_dashboard
    assert len(gather_calls) == 1
    assert len(gather_calls[0].args) == 2
    assert all(isinstance(argument, ast.Call) for argument in gather_calls[0].args)
    assert not any(
        isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp))
        for node in ast.walk(gather_calls[0])
    )


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
