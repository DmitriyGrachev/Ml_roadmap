"""Supplied candidate arithmetic is reproducible; validity needs investigation."""

import importlib
import json
from pathlib import Path

import pytest


def test_candidate_is_reproducible_and_predictions_explain_score(tmp_path: Path) -> None:
    candidate = importlib.import_module(__package__ + ".candidate")
    first = candidate.run_candidate(tmp_path / "a")
    second = candidate.run_candidate(tmp_path / "b")
    assert first.read_bytes() == second.read_bytes()
    for artifact in ("data.json", "split.json", "predictions.json"):
        assert (first.parent / artifact).read_bytes() == (second.parent / artifact).read_bytes()
    result = json.loads(first.read_text())
    data = json.loads((first.parent / "data.json").read_text())
    labels = {row["id"]: row["label"] for row in data}
    records = json.loads((first.parent / "predictions.json").read_text())
    split = json.loads((first.parent / "split.json").read_text())
    assert [row["id"] for row in records] == split["test_ids"]
    assert not {row["id"] for row in records}.intersection(split["train_ids"])
    correct = sum(labels[r["id"]] == r["prediction"] for r in records)
    assert result["accuracy"] == correct / len(records)
    assert result["accuracy"] >= 0.9
    assert len({r["id"] for r in records}) == len(records)
    with pytest.raises(FileExistsError):
        candidate.run_candidate(first.parent)


def test_fixture_is_deterministic_and_contains_unique_rows() -> None:
    fixture = importlib.import_module(__package__ + ".fixture")
    rows = json.loads(fixture.dataset_bytes())
    assert fixture.dataset_bytes() == fixture.dataset_bytes()
    assert len(rows) >= 40
    assert len({row["id"] for row in rows}) == len(rows)
    assert {row["label"] for row in rows} == {0, 1}


@pytest.mark.parametrize("artifact", ["data.json", "split.json", "predictions.json", "train_id"])
def test_candidate_contract_rejects_equal_metric_artifact_mutations(
    artifact: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = importlib.import_module(__package__ + ".candidate")
    real_run = candidate.run_candidate

    def changed_run(output: Path) -> Path:
        result: Path = real_run(output)
        if artifact == "train_id":
            data = json.loads((output / "data.json").read_text())
            split = json.loads((output / "split.json").read_text())
            predictions_path = output / "predictions.json"
            predictions = json.loads(predictions_path.read_text())
            labels = {row["id"]: row["label"] for row in data}
            predictions[0]["id"] = next(
                key for key in split["train_ids"] if labels[key] == predictions[0]["prediction"]
            )
            predictions_path.write_text(json.dumps(predictions), encoding="utf-8")
        elif output.name == "b":
            path = output / artifact
            value = json.loads(path.read_text())
            if artifact == "split.json":
                value["train_ids"].reverse()
            else:
                value.reverse()
            path.write_text(json.dumps(value), encoding="utf-8")
        return result

    monkeypatch.setattr(candidate, "run_candidate", changed_run)
    with pytest.raises(AssertionError):
        test_candidate_is_reproducible_and_predictions_explain_score(tmp_path)
