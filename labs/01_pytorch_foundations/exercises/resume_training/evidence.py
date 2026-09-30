"""Read-only replay of local resume evidence; human review remains required."""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity

from . import fixture


def replay_inference(
    state: dict[str, Any],
    snapshot: list[dict[str, Any]],
    saved: dict[str, Any],
) -> None:
    """Actually evaluate saved tensors against the local validation snapshot."""
    try:
        fixture.assert_same(snapshot, fixture.SNAPSHOT)
        model = fixture.build_model()
        model.load_state_dict(state, strict=True)
        model.eval()
        with torch.no_grad():
            features = torch.tensor([r["features"] for r in snapshot[-2:]], dtype=torch.float32)
            observed = {"ids": [r["id"] for r in snapshot[-2:]], "logits": model(features)}
        fixture.assert_same(observed, saved)
    except (AssertionError, RuntimeError, KeyError, TypeError) as exc:
        raise ValueError("inference differs from saved weights/snapshot") from exc


def validate_traces(continuous: dict[str, Any], resumed: dict[str, Any]) -> None:
    """Replay deterministic continuous training, rather than trusting matching saved losses."""
    model, optimizer, cursor = fixture.new_run()
    cursor, trace = fixture.advance(model, optimizer, cursor, 7)
    expected = fixture.result(model, optimizer, cursor, trace)
    try:
        if any(saved["next_rng"] != expected["next_rng"] for saved in (continuous, resumed)):
            raise ValueError("trace next RNG draws must match exactly")
        for key in ("trace", "model", "optimizer", "cursor", "identity", "next_rng", "inference"):
            fixture.assert_same(expected[key], continuous[key])
            fixture.assert_same(expected[key], resumed[key])
    except (AssertionError, KeyError, TypeError) as exc:
        raise ValueError("trace does not reproduce the fixture trajectory") from exc


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid evidence JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest must be a mapping")
    return value


def validate_evidence(root: Path) -> str:
    """Check bytes/identity, checkpoint, fresh resume, full traces and local inference.

    Uses fresh temporary outputs only. Successful consistency is not evidence of
    generalization, learner authorship, or a completed oral explanation.
    """
    manifest = _read(root / "manifest.json")
    validate_identity(
        manifest,
        exercise_id="lab-training-resume",
        dataset_sha256=fixture.IDENTITY["data"],
        split_sha256=fixture.IDENTITY["split"],
    )
    snapshot_path = checked_artifact(root, "snapshot.json", manifest["dataset_sha256"])
    split_path = checked_artifact(root, "split.json", manifest["split_sha256"])
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        fixture.assert_same(snapshot, fixture.SNAPSHOT)
        fixture.assert_same(json.loads(split_path.read_text(encoding="utf-8")), fixture.SPLIT)
        fixture.assert_same(manifest["config"], fixture.CONFIG)
    except (AssertionError, ValueError, TypeError) as exc:
        raise ValueError("snapshot/config/split identity differs") from exc
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("artifact hashes are required")
    paths = {
        name: checked_artifact(root, name, artifacts.get(name, ""))
        for name in ("continuous.pt", "resumed.pt", "checkpoint.pt")
    }
    if (
        manifest.get("review_status") != "REQUIRES_REVIEW"
        or not isinstance(manifest.get("explanation"), str)
        or not manifest["explanation"].strip()
    ):
        raise ValueError("student explanation and REQUIRES_REVIEW are required")
    continuous, resumed, checkpoint = (
        fixture.load_checkpoint(paths[name])
        for name in ("continuous.pt", "resumed.pt", "checkpoint.pt")
    )
    validate_traces(continuous, resumed)
    for saved in (continuous, resumed):
        replay_inference(saved["model"], snapshot, saved["inference"])
    # Check the actual interruption artifact against its independently executed prefix.
    model, optimizer, cursor = fixture.new_run()
    cursor, prefix = fixture.advance(model, optimizer, cursor, 3)
    try:
        fixture.assert_same(checkpoint["model"], model.state_dict())
        fixture.assert_same(checkpoint["optimizer"], optimizer.state_dict())
        fixture.assert_same(checkpoint["cursor"], asdict(cursor))
        fixture.assert_same(checkpoint["identity"], fixture.IDENTITY)
        if set(checkpoint["rng"]) != {"python", "numpy", "torch"}:
            raise ValueError("checkpoint RNG is incomplete")
    except (AssertionError, KeyError, TypeError) as exc:
        raise ValueError("checkpoint differs from the step-3 interruption") from exc
    # This deliberately depends on the student's restore_state, never a hidden solution.
    with tempfile.TemporaryDirectory(prefix="resume-replay-") as temporary:
        replayed = fixture.fresh_run(
            Path(temporary) / "replayed.pt", checkpoint=paths["checkpoint.pt"]
        )
    replayed["trace"] = prefix + replayed["trace"]
    validate_traces(continuous, replayed)
    return "REQUIRES_REVIEW"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(validate_evidence(args.root))


if __name__ == "__main__":
    main()
