"""Negative evidence checks and local replay, without a reference resume solution."""

import hashlib
import json
from copy import deepcopy
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from roadmap_tools.exercise import exercise_call

torch = pytest.importorskip("torch", reason="Install the optional training group")
fixture = import_module("labs.01_pytorch_foundations.exercises.resume_training.fixture")
evidence = import_module("labs.01_pytorch_foundations.exercises.resume_training.evidence")
starter = import_module("labs.01_pytorch_foundations.exercises.resume_training.starter")


def continuous() -> dict[str, Any]:
    model, optimizer, cursor = fixture.new_run()
    cursor, trace = fixture.advance(model, optimizer, cursor, 7)
    return dict(fixture.result(model, optimizer, cursor, trace))


def test_inference_replays_actual_weights_on_snapshot() -> None:
    model = fixture.build_model()
    observed = fixture.inference(model)
    evidence.replay_inference(model.state_dict(), fixture.SNAPSHOT, observed)
    wrong = deepcopy(observed)
    wrong["logits"][0, 0] += 0.5
    with pytest.raises(ValueError, match="inference"):
        evidence.replay_inference(model.state_dict(), fixture.SNAPSHOT, wrong)


@pytest.mark.parametrize(
    "mutation", ["replay", "loss", "ids", "step", "optimizer", "rng", "rng_small"]
)
def test_saved_traces_cannot_agree_on_the_same_false_story(mutation: str) -> None:
    saved = continuous()
    if mutation == "replay":
        saved["trace"][3] = deepcopy(saved["trace"][2])
    elif mutation == "loss":
        saved["trace"][1]["loss"] += 0.5
    elif mutation == "ids":
        saved["trace"][0]["ids"].reverse()
    elif mutation == "step":
        saved["trace"][0]["global_step"] = 0
    elif mutation == "optimizer":
        saved["optimizer"]["state"][0]["momentum_buffer"].zero_()
    elif mutation == "rng":
        saved["next_rng"][1] += 0.25
    else:
        saved["next_rng"][1] += 1e-8
    with pytest.raises(ValueError, match="trace"):
        evidence.validate_traces(saved, deepcopy(saved))


def test_continuous_trace_replay_is_not_resume_credit() -> None:
    saved = continuous()
    # Component check only. Full evidence also requires a real step-3 checkpoint
    # and fresh-process continuation through the student's restore_state.
    evidence.validate_traces(saved, deepcopy(saved))


def manifest_files(root: Path) -> dict[str, Any]:
    for name, value in (("snapshot.json", fixture.SNAPSHOT), ("split.json", fixture.SPLIT)):
        (root / name).write_bytes(fixture.canonical_bytes(value))
    return {
        "schema_version": 1,
        "exercise_id": "lab-training-resume",
        "dataset_sha256": fixture.IDENTITY["data"],
        "split_sha256": fixture.IDENTITY["split"],
        "config": fixture.CONFIG,
        "artifacts": {},
        "review_status": "REQUIRES_REVIEW",
        "explanation": "Temporary negative test only; no learner report.",
    }


def test_missing_checkpoint_is_not_verified(tmp_path: Path) -> None:
    manifest = manifest_files(tmp_path)
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="artifact"):
        evidence.validate_evidence(tmp_path)


def test_foreign_snapshot_even_with_updated_digest_is_rejected(tmp_path: Path) -> None:
    manifest = manifest_files(tmp_path)
    foreign = deepcopy(fixture.SNAPSHOT)
    foreign[0]["features"][0] += 1
    payload = fixture.canonical_bytes(foreign)
    (tmp_path / "snapshot.json").write_bytes(payload)
    manifest["dataset_sha256"] = hashlib.sha256(payload).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=r"identity|snapshot"):
        evidence.validate_evidence(tmp_path)


def test_changed_snapshot_bytes_are_rejected(tmp_path: Path) -> None:
    manifest = manifest_files(tmp_path)
    (tmp_path / "snapshot.json").write_text("[]", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="sha256"):
        evidence.validate_evidence(tmp_path)


def test_actual_student_checkpoint_drives_complete_evidence_replay(tmp_path: Path) -> None:
    baseline = fixture.fresh_run(tmp_path / "continuous.pt")
    model, optimizer, cursor = fixture.new_run()
    cursor, prefix = fixture.advance(model, optimizer, cursor, 3)
    state = exercise_call(starter.capture_state, model, optimizer, cursor, fixture.IDENTITY)
    fixture.save_checkpoint(tmp_path / "checkpoint.pt", state)
    other_model, other_optimizer, _ = fixture.new_run(999)
    exercise_call(starter.restore_state, other_model, other_optimizer, state, fixture.IDENTITY)
    resumed = fixture.fresh_run(tmp_path / "suffix.pt", checkpoint=tmp_path / "checkpoint.pt")
    resumed["trace"] = prefix + resumed["trace"]
    fixture.save_checkpoint(tmp_path / "resumed.pt", resumed)
    manifest = manifest_files(tmp_path)
    manifest["artifacts"] = {
        name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in ("continuous.pt", "resumed.pt", "checkpoint.pt")
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert baseline["next_rng"] == resumed["next_rng"]
    assert evidence.validate_evidence(tmp_path) == "REQUIRES_REVIEW"


def test_learner_evidence_is_present_and_replayable() -> None:
    root = fixture.REPOSITORY / "generated-reports/training-resume"
    if not (root / "manifest.json").exists():
        pytest.xfail("Learner resume artifacts have not been submitted")
    assert evidence.validate_evidence(root) == "REQUIRES_REVIEW"
