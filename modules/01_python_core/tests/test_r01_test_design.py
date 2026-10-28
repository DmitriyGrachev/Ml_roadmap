"""Author checks of teacher behavior, never acceptance for the new manual practice."""

import runpy
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

LESSON = Path(__file__).parents[1] / "09_testing"
REPOSITORY = LESSON.parents[2]


@pytest.fixture
def lesson() -> dict[str, Any]:
    return runpy.run_path(str(LESSON / "walkthrough.py"))


@pytest.mark.parametrize(
    ("text", "limit", "want"),
    [
        ("atlas", 3, "atl"),
        ("", 4, ""),
        ("atlas", 0, ""),
        ("atlas", 5, "atlas"),
        ("atlas", 6, "atlas"),
    ],
)
def test_preview_follows_character_limit(
    lesson: dict[str, Any], text: str, limit: int, want: str
) -> None:
    assert lesson["preview"](text, limit) == want


@pytest.mark.parametrize(
    ("text", "limit"), [("atlas", -1), ("atlas", True), ("atlas", 1.5), (None, 3)]
)
def test_preview_rejects_inputs_outside_contract(
    lesson: dict[str, Any], text: object, limit: object
) -> None:
    with pytest.raises(ValueError, match=r"text|limit"):
        lesson["preview"](text, limit)


def test_paragraph_decomposition_is_local_ordered_and_does_not_count_blank_paragraphs(
    lesson: dict[str, Any],
) -> None:
    summarize = lesson["paragraph_word_counts"]
    assert summarize("red blue\n\ngreen\nleaf\n\n  ") == (2, 2)
    assert summarize("one") == (1,)
    assert summarize("") == ()


def test_debugging_demo_exits_unsuccessfully_and_shows_actual_failing_call_stack() -> None:
    result = subprocess.run(
        [sys.executable, str(LESSON / "debugging/empty_preview/broken.py")],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert 'main: inspect_document("")' in result.stdout
    assert "inspect_document: return broken_preview(text, 4)" in result.stdout
    assert "broken_preview: return text[0] + text[1:limit]" in result.stdout
    assert "IndexError: string index out of range" in result.stdout


@pytest.fixture
def populated_practice_copy(tmp_path: Path) -> tuple[Path, Path]:
    """Simulate future learner work only in a copy, never in the real empty file."""
    copied_lesson = tmp_path / "lesson"
    shutil.copytree(LESSON, copied_lesson, ignore=shutil.ignore_patterns("__pycache__"))
    practice = copied_lesson / "practice/document_outline"
    cases = next(practice.glob("*outline*.py"))
    cases.write_text(
        "def test_independent_outline_case():\n    assert 1 + 1 == 3\n", encoding="utf-8"
    )
    return copied_lesson, cases


def test_manual_practice_runs_only_by_explicit_path_when_populated(
    populated_practice_copy: tuple[Path, Path],
) -> None:
    copied_lesson, cases = populated_practice_copy
    explicit = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(REPOSITORY / "pyproject.toml"),
            str(cases),
            "-q",
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert explicit.returncode == 1, explicit.stdout + explicit.stderr
    assert "test_independent_outline_case" in explicit.stdout
    assert "1 failed" in explicit.stdout

    directory = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(REPOSITORY / "pyproject.toml"),
            str(copied_lesson),
            "-q",
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert directory.returncode == 0, directory.stdout + directory.stderr
