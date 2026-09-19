from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from roadmap_tools.cli import _main


def write_catalog(root: Path) -> None:
    (root / "curriculum.toml").write_text(
        """
[[items]]
id = "python-first"
title = "First Python lesson"
kind = "lesson"
readme = "modules/first/README.md"
tests = ["tests/first_test.py"]

[[items]]
id = "python-second"
title = "Second Python lesson"
kind = "lesson"
readme = "modules/second/README.md"
tests = ["tests/second test.py"]
""",
        encoding="utf-8",
    )


def make_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository with spaces"
    for module in ("first", "second"):
        readme = root / "modules" / module / "README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(f"# {module}\n", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir(parents=True)
    (tests / "first_test.py").write_text("", encoding="utf-8")
    (tests / "second test.py").write_text("", encoding="utf-8")
    write_catalog(root)
    return root


def unexpected_runner(command: Sequence[str]) -> int:
    raise AssertionError(f"Unexpected subprocess command: {command!r}")


def test_list_prints_catalog_items_in_toml_order(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_repository(tmp_path)

    exit_code = _main(["list"], root, unexpected_runner)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.index("python-first") < output.index("python-second")


def test_list_reports_empty_catalog_without_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "empty repository"
    root.mkdir()
    (root / "curriculum.toml").write_text("items = []\n", encoding="utf-8")

    exit_code = _main(["list"], root, unexpected_runner)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No catalog items are currently available." in output


def test_status_reports_checklist_states_from_progress_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_repository(tmp_path)
    (root / "progress.md").write_text(
        """# Progress
- [ ] Start the first lesson
- [~] Work through an exercise
- [x] Complete the recap
- [X] Ignore this unsupported marker
""",
        encoding="utf-8",
    )

    exit_code = _main(["status"], root, unexpected_runner)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "[ ] Start the first lesson" in output
    assert "[~] Work through an exercise" in output
    assert "[x] Complete the recap" in output
    assert "Ignore this unsupported marker" not in output


def test_unknown_identifier_returns_suggestion(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_repository(tmp_path)

    exit_code = _main(["test", "python-frist"], root, unexpected_runner)

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "python-first" in output


def test_runs_item_tests_as_argument_list_and_preserves_success(tmp_path: Path) -> None:
    root = make_repository(tmp_path)
    commands: list[Sequence[str]] = []

    def runner(command: Sequence[str]) -> int:
        commands.append(command)
        return 0

    exit_code = _main(["test", "python-second"], root, runner)

    assert exit_code == 0
    assert commands == [[sys.executable, "-m", "pytest", str(root / "tests" / "second test.py")]]


def test_preserves_pytest_exit_code(tmp_path: Path) -> None:
    root = make_repository(tmp_path)

    exit_code = _main(["test", "python-first"], root, lambda command: 5)

    assert exit_code == 5
