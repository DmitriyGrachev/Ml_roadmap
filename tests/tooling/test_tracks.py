"""A route composes existing catalog scopes without manufacturing learner credit."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from roadmap_tools.cli import _main
from roadmap_tools.tracks import TrackError, load_tracks


def repository(tmp_path: Path, required: str = '["first", "second"]') -> Path:
    (tmp_path / "review.md").write_text("# Human review\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Lesson\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    for name in ("one", "two"):
        (tests / f"test_{name}.py").write_text("", encoding="utf-8")
    (tmp_path / "curriculum.toml").write_text(
        '[[items]]\nid="first"\ntitle="First"\nkind="lesson"\n'
        'readme="README.md"\ntests=["tests"]\n'
        '[[items]]\nid="second"\ntitle="Second"\nkind="exercise"\n'
        'readme="README.md"\ntests=["tests/test_two.py"]\n',
        encoding="utf-8",
    )
    (tmp_path / "learning_tracks.toml").write_text(
        f'[[tracks]]\nid="route"\ntitle="Route"\nreview="review.md"\nrequired={required}\n',
        encoding="utf-8",
    )
    return tmp_path


def test_route_keeps_order_and_review_path(tmp_path: Path) -> None:
    track = load_tracks(repository(tmp_path))["route"]
    assert track.required == ("first", "second")
    assert track.review == tmp_path / "review.md"


@pytest.mark.parametrize("required", ['["missing"]', '["first", "first"]', "[]"])
def test_route_rejects_unknown_duplicate_and_empty_requirements(
    tmp_path: Path, required: str
) -> None:
    with pytest.raises(TrackError):
        load_tracks(repository(tmp_path, required))


def test_review_path_cannot_escape_checkout(tmp_path: Path) -> None:
    root = repository(tmp_path)
    path = root / "learning_tracks.toml"
    path.write_text(path.read_text().replace('review="review.md"', 'review="../outside.md"'))
    with pytest.raises(TrackError):
        load_tracks(root)


def test_check_track_preserves_failure_and_does_not_write_progress(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repository(tmp_path)
    progress = root / "progress.md"
    progress.write_text("- [ ] first\n", encoding="utf-8")
    commands: list[list[str]] = []

    def failed(command: Sequence[str]) -> int:
        commands.append(list(command))
        return 1

    assert _main(["check-track", "route"], root, failed) == 1
    assert commands == [
        [sys.executable, "-m", "pytest", "-p", "roadmap_tools.strict_check", str(root / "tests")]
    ]
    assert "PASSED" not in capsys.readouterr().out
    assert progress.read_text() == "- [ ] first\n"


def test_technical_pass_still_requires_human_review(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _main(["check-track", "route"], repository(tmp_path), lambda command: 0) == 0
    output = capsys.readouterr().out
    assert "TECHNICAL CHECKS PASSED" in output
    assert "HUMAN REVIEW REQUIRED" in output


def test_track_is_read_only_and_inventory_uses_catalog(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repository(tmp_path)

    def unexpected(command: object) -> int:
        raise AssertionError(command)

    assert _main(["track", "route"], root, unexpected) == 0
    output = capsys.readouterr().out
    assert output.index("first") < output.index("second")
    assert "review.md" in output
    assert _main(["inventory"], root, unexpected) == 0
    assert "total: 2" in capsys.readouterr().out


def test_registered_routes_put_new_explanations_before_dependent_practice() -> None:
    root = Path(__file__).resolve().parents[2]
    tracks = load_tracks(root)
    for track in tracks.values():
        for before, after in (
            ("python-async-lifecycle", "python-bounded-fetch"),
            ("ml-gradient-derivations", "lab-pytorch"),
            ("data-training-stability", "ml-external-tabular"),
            ("lab-huggingface", "document-external-model-study"),
            ("document-external-model-study", "production-service-lifecycle"),
        ):
            assert track.required.index(before) < track.required.index(after), track.identifier
    applied = tracks["applied-ai"].required
    assert applied.index("rag-evaluation") < applied.index("rag-end-to-end-evaluation")
