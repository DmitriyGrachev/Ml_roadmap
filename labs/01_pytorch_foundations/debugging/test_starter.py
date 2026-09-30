"""Correction must produce reproducible behavior, never an asserted success flag."""

import json
import shutil
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

pytest.importorskip("torch", reason="Install the optional training group")
starter = import_module("labs.01_pytorch_foundations.debugging.starter")
fixtures = import_module("labs.01_pytorch_foundations.debugging.fixtures")
evidence = import_module("labs.01_pytorch_foundations.debugging.evidence")


def check_investigation(case_id: str, output_dir: Path) -> None:
    expected_root = output_dir.resolve()
    assert not output_dir.exists(), "fresh output destination already exists"
    assert not output_dir.is_symlink(), "fresh output destination is a symlink"
    assert not output_dir.is_junction(), "fresh output destination is a junction"
    root = exercise_call(starter.investigate, case_id, output_dir)
    assert isinstance(root, Path)
    assert root.resolve() == expected_root, "returned root is not the designated fresh output"
    source = (root / "after" / "source.py").resolve(strict=True)
    assert source.is_relative_to(expected_root), "student source escapes the fresh output"
    evidence.validate_evidence(root, trusted_student_source=source)
    before = fixtures.load_run(root / "before")
    after = fixtures.load_run(root / "after")
    assert before["case_id"] == after["case_id"] == case_id
    with pytest.raises(AssertionError):
        fixtures.assert_healthy(before)
    fixtures.assert_healthy(after)


@pytest.mark.parametrize("case_id", ["a", "b", "c", "d"])
def test_investigation_replays_and_meets_behavior_contract(case_id: str, tmp_path: Path) -> None:
    check_investigation(case_id, tmp_path / "investigation")


def directory_link(link: Path, target: Path) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
        )
    else:
        link.symlink_to(target, target_is_directory=True)


@pytest.mark.parametrize("returned_location", ["external", "root_link", "source_link"])
def test_automatic_trust_refuses_stale_external_output(
    returned_location: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from .test_evidence import make_investigation

    investigation = make_investigation(tmp_path)
    marker = tmp_path / "executed.txt"
    source = investigation / "after" / "source.py"
    with source.open("a", encoding="utf-8") as stream:
        stream.write(f"\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n")
    manifest_path = investigation / "after" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["source.py"] = fixtures.digest(source.read_bytes())
    manifest_path.write_bytes(fixtures.canonical(manifest))

    def return_saved(case_id: str, output_dir: Path) -> Path:
        if returned_location == "external":
            return investigation
        if returned_location == "root_link":
            directory_link(output_dir, investigation)
        else:
            output_dir.mkdir()
            shutil.copytree(investigation / "before", output_dir / "before")
            shutil.copyfile(investigation / "report.json", output_dir / "report.json")
            directory_link(output_dir / "after", investigation / "after")
        return output_dir

    monkeypatch.setattr(starter, "investigate", return_saved)
    with pytest.raises(AssertionError, match="fresh output"):
        check_investigation("a", tmp_path / "fresh-investigation")
    assert not marker.exists()
