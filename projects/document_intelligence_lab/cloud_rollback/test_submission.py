"""Offline grading of private evidence; this test never contacts AWS."""

import os
from pathlib import Path

import pytest

from ..artifacts import file_sha256, load_trusted_local_classifier, predict_documents, read_json
from .capture import verify_run


@pytest.mark.student_exercise
def test_learner_cloud_rollback() -> None:
    location = os.environ.get("ROADMAP_CLOUD_ROLLBACK_EVIDENCE")
    if not location:
        pytest.xfail("Run your ECS rollback and set ROADMAP_CLOUD_ROLLBACK_EVIDENCE")
    run = Path(location)
    expected = read_json(run / "expect.json")
    for key in ("a", "b"):
        root = run / key / "bundle"
        digest = file_sha256(root / "manifest.json")
        local = load_trusted_local_classifier(root, digest)
        assert expected[key] == {
            "bundle_sha256": digest,
            "predicted_label": predict_documents(local, [expected["probe"]])[0],
            "model_id": local.bundle.manifest["model"]["id"],
            "preprocessing_version": local.bundle.manifest["preprocessing"]["version"],
        }
    verify_run(run)
    assert read_json(run / "tasks-after.json")["taskArns"] == []
    deleted = read_json(run / "deleted.json")["Stacks"]
    assert len(deleted) == 1
    assert deleted[0]["StackId"] == read_json(run / "stack.json")["StackId"]
    assert deleted[0]["StackStatus"] == "DELETE_COMPLETE"
    assert (run / "defense.md").read_text(encoding="utf-8").strip()
