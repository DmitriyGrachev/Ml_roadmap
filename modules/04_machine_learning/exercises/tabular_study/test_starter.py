"""Learner output must replay; a manifest filename alone is not completion."""

import json
from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

from .evidence import validate_evidence
from .fixture import make_fixture
from .starter import run_experiment

pytestmark = pytest.mark.student_exercise


def test_study_returns_local_replayable_manifest(tmp_path: Path) -> None:
    data_path = tmp_path / "support.csv"
    make_fixture(23).to_csv(data_path, index=False)
    output = tmp_path / "study"
    check_study(data_path, output, seed=23)


def check_study(data_path: Path, output: Path, *, seed: int) -> None:
    expected_root = output.resolve()
    expected_input = data_path.read_bytes()
    assert not output.exists(), "fresh output already exists"
    assert not output.is_symlink(), "fresh output is a symlink"
    assert not output.is_junction(), "fresh output is a junction"
    manifest_path = exercise_call(run_experiment, data_path, output, seed=seed)
    assert not output.is_symlink(), "fresh output became a symlink"
    assert not output.is_junction(), "fresh output became a junction"
    assert output.is_dir(), "fresh output directory was not created"
    assert output.resolve(strict=True) == expected_root, "fresh output was redirected"
    assert manifest_path.resolve() == expected_root / "manifest.json", "fresh output mismatch"
    model_path = (output / "model.pkl").resolve(strict=True)
    assert model_path == expected_root / "model.pkl", "model escapes fresh output"
    assert model_path.is_file(), "model must be a regular file"
    assert data_path.read_bytes() == expected_input, "input dataset was changed"
    assert (output / "dataset.csv").read_bytes() == expected_input, "dataset differs from input"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["config"]["seed"] == seed
    assert 4 <= len(manifest["config"]["candidates"]) <= 12
    assert {c["family"] for c in manifest["config"]["candidates"]} >= {
        "Dummy",
        "LogisticRegression",
        "TreeOrRandomForest",
        "HistGradientBoostingClassifier",
    }
    # Only this test's own locally executed student run grants loading permission.
    validate_evidence(output, trusted_model_path=model_path)


def test_study_preserves_existing_output(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    make_fixture(1).to_csv(path, index=False)
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "notes.txt"
    marker.write_text("learner work", encoding="utf-8")
    with pytest.raises(FileExistsError):
        exercise_call(run_experiment, path, output, seed=1)
    assert marker.read_text(encoding="utf-8") == "learner work"
