"""Real learner artifacts, repeatability, preservation and observable page consumption."""

import importlib
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import pytest

from roadmap_tools.exercise import exercise_call

from .evidence import validate_evidence
from .starter import build_release

pytestmark = pytest.mark.student_exercise
FIXTURES = Path(__file__).with_name("fixtures")
INPUTS = tuple(
    FIXTURES / name for name in ("source_a.csv", "source_b.jsonl", "labels.csv", "provenance.json")
)


def test_release_has_real_coverage_and_repeats_in_fresh_directory(tmp_path: Path) -> None:
    original_inputs = {path: path.read_bytes() for path in INPUTS}
    directories = [tmp_path / "first", tmp_path / "repeat"]
    for directory in directories:
        manifest = exercise_call(build_release, INPUTS, directory, batch_size=2)
        assert manifest == directory / "manifest.json"
        assert validate_evidence(directory, input_dir=FIXTURES) == "REQUIRES_REVIEW"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["counts"] == {"accepted": 2, "rejected": 3, "review": 3}
        assert data["config"]["batch_size"] == 2
    # No timestamps or absolute output paths may perturb published artifact bytes.
    names = {
        "manifest.json",
        "accepted.jsonl",
        "rejected.jsonl",
        "review.jsonl",
        "splits.json",
        "schema.json",
        "memory.md",
    }
    assert {name: (directories[0] / name).read_bytes() for name in names} == {
        name: (directories[1] / name).read_bytes() for name in names
    }
    assert {path: path.read_bytes() for path in INPUTS} == original_inputs


def test_existing_output_is_never_appended_or_overwritten(tmp_path: Path) -> None:
    marker = tmp_path / "notes.txt"
    marker.write_text("learner work", encoding="utf-8")
    with pytest.raises(FileExistsError):
        exercise_call(build_release, INPUTS, tmp_path, batch_size=2)
    assert marker.read_text(encoding="utf-8") == "learner work"


@pytest.mark.parametrize("batch_size", [0, -1])
def test_invalid_budget_is_rejected_before_output(tmp_path: Path, batch_size: int) -> None:
    target = tmp_path / "invalid"
    with pytest.raises(ValueError, match="batch_size"):
        exercise_call(build_release, INPUTS, target, batch_size=batch_size)
    assert not target.exists()


def test_page_observations_do_not_certify_total_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_property: Any,
) -> None:
    pages = importlib.import_module("modules.01_python_core.exercises.paged_stream.starter")
    original = pages.iter_pages
    observations: list[tuple[int, int]] = []

    def observed(source: Iterable[Any], size: int) -> Iterator[tuple[Any, ...]]:
        consumed = 0

        def counted() -> Iterator[Any]:
            nonlocal consumed
            for row in source:
                consumed += 1
                yield row

        yielded = 0
        for page in original(counted(), size):
            assert size == 2
            assert 0 < len(page) <= 2
            yielded += len(page)
            # Observes read-ahead at this boundary, not hidden retention downstream.
            assert consumed == yielded
            observations.append((consumed, len(page)))
            yield page

    monkeypatch.setattr(pages, "iter_pages", observed)
    output = tmp_path / "observed"
    manifest = exercise_call(build_release, INPUTS, output, batch_size=2)
    assert validate_evidence(output, input_dir=FIXTURES) == "REQUIRES_REVIEW"
    resources = json.loads(manifest.read_text(encoding="utf-8"))["resources"]
    assert resources["peak_buffer_records"] <= 2 * resources["buffer_limit_pages"]
    # Different internal boundaries are permitted; absence of observations is explicit.
    record_property("observed_pages", len(observations))
    record_property("page_evidence", "observed" if observations else "not_observed")
    record_property("memory_conclusion", "REQUIRES_REVIEW")
