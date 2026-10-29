"""Strict learner checks explain optional environments without importing frameworks."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from importlib.machinery import ModuleSpec
from pathlib import Path

import pytest

from roadmap_tools.catalog import Catalog, CatalogError
from roadmap_tools.cli import _main


def repository(tmp_path: Path, fields: str = "") -> Path:
    (tmp_path / "README.md").write_text("# Practice\n", encoding="utf-8")
    (tmp_path / "test_student.py").write_text("", encoding="utf-8")
    (tmp_path / "curriculum.toml").write_text(
        '[[items]]\nid="practice"\ntitle="Practice"\nkind="exercise"\n'
        'readme="README.md"\ntests=["test_student.py"]\n' + fields,
        encoding="utf-8",
    )
    (tmp_path / "learning_tracks.toml").write_text(
        '[[tracks]]\nid="route"\ntitle="Route"\nreview="README.md"\nrequired=["practice"]\n',
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.parametrize(
    "field",
    [
        '"trainer"',
        '["unknown"]',
        '["trainer", "trainer"]',
        "[1]",
        "[true]",
        '[""]',
    ],
)
def test_catalog_rejects_invalid_optional_groups(tmp_path: Path, field: str) -> None:
    with pytest.raises(CatalogError, match="requires_groups"):
        Catalog.load(repository(tmp_path, f"requires_groups = {field}\n"))


def test_catalog_preserves_declared_groups_and_legacy_default(tmp_path: Path) -> None:
    root = repository(tmp_path, 'requires_groups = ["trainer", "sft"]\n')
    item = Catalog.load(root).get("practice")
    assert item.requires_groups == ("trainer", "sft")
    assert not item.requires_training
    repository(tmp_path)
    assert Catalog.load(root).get("practice").requires_groups == ()


def test_strict_check_reports_entire_environment_and_never_runs_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repository(tmp_path, 'requires_groups = ["trainer", "sft"]\n')
    seen: list[str] = []

    def availability(name: str) -> ModuleSpec | None:
        seen.append(name)
        return None if name in {"trl", "accelerate"} else ModuleSpec(name, loader=None)

    monkeypatch.setattr(importlib.util, "find_spec", availability)

    def unexpected(command: Sequence[str]) -> int:
        raise AssertionError(f"Must not start incomplete environment: {command}")

    assert _main(["check", "practice"], root, unexpected) == 2
    output = capsys.readouterr().out
    assert "accelerate" in output
    assert "trl" in output
    assert "uv sync --locked --group trainer --group sft" in output
    assert all("." not in name for name in seen)
    assert len(seen) == len(set(seen))


def test_health_test_can_skip_uninstalled_optional_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path, 'requires_groups = ["ranking"]\n')

    def unexpected(name: str) -> None:
        raise AssertionError(f"Health command must delegate to pytest: {name}")

    monkeypatch.setattr(importlib.util, "find_spec", unexpected)
    assert _main(["test", "practice"], root, lambda command: 5) == 5


def test_available_strict_environment_preserves_pytest_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path, 'requires_groups = ["experiments"]\n')
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: ModuleSpec(name, loader=None))
    commands: list[Sequence[str]] = []

    def failed(command: Sequence[str]) -> int:
        commands.append(command)
        return 1

    assert _main(["check", "practice"], root, failed) == 1
    assert commands == [
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "roadmap_tools.strict_check",
            str(root / "test_student.py"),
        ]
    ]


def test_track_unions_legacy_training_and_new_groups_with_migrations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repository(
        tmp_path, 'requires_training = true\nrequires_groups = ["ranking", "experiments"]\n'
    )
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)

    def unexpected(command: Sequence[str]) -> int:
        raise AssertionError(command)

    assert _main(["check-track", "route"], root, unexpected) == 2
    output = capsys.readouterr().out
    assert output.count("uv sync") == 1
    for group in ("training", "migrations", "ranking", "experiments"):
        assert f"--group {group}" in output


def test_ranking_group_checks_transitive_training_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repository(tmp_path, 'requires_groups = ["ranking"]\n')
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name: None if name == "torch" else ModuleSpec(name, loader=None),
    )

    def unexpected(command: Sequence[str]) -> int:
        raise AssertionError(command)

    assert _main(["check", "practice"], root, unexpected) == 2
    output = capsys.readouterr().out
    assert "torch" in output
    assert "--group ranking" in output
