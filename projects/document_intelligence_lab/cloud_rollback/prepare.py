"""Build two local, reload-verified rules image contexts for a chosen synthetic probe."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import Any

from ..artifacts import (
    file_sha256,
    json_bytes,
    load_trusted_local_classifier,
    predict_documents,
    write_run_new,
)
from ..contracts import normalize_document


def prepare(source: Path, output: Path, probe: str, b_label: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9]{3,39}", probe):
        raise ValueError("choose a 4..40 character synthetic lowercase ASCII token")
    baseline = load_trusted_local_classifier(source, file_sha256(source / "manifest.json"))
    bundle = baseline.bundle
    if any(probe in normalize_document(row.text).split() for row in bundle.dataset.records):
        raise ValueError("the probe token must be new to this fixture")
    if any(rule["token"] == probe for rule in baseline.model["rules"]):
        raise ValueError("the probe token is already a rule")
    if b_label not in bundle.dataset.labels or predict_documents(baseline, [probe]) == [b_label]:
        raise ValueError("choose an existing B label different from A's result")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(source, output / "a" / "bundle")
    model_b = {
        **baseline.model,
        "rules": [*baseline.model["rules"], {"token": probe, "label": b_label}],
    }
    ids = bundle.splits["test"]
    texts = [bundle.dataset.by_id[row].text for row in ids]
    started = perf_counter()
    labels = predict_documents(replace(baseline, model=model_b), texts)
    seconds = perf_counter() - started
    manifest = bundle.manifest
    code_hash = hashlib.sha256(
        (manifest["code"]["source_sha256"] + file_sha256(Path(__file__))).encode("ascii")
    ).hexdigest()
    changed = {
        **manifest,
        "exercise_id": "document-cloud-rollback",
        "evidence_kind": "LOCAL_SYNTHETIC_IMAGE_INPUT",
        "run_id": manifest["run_id"] + "-probe",
        "code": {**manifest["code"], "source_sha256": code_hash},
        "config": {"seed": manifest["config"]["seed"], "added_rule": model_b["rules"][-1]},
        "model": {**manifest["model"], "id": manifest["model"]["id"] + "-probe", "revision": "2"},
    }
    write_run_new(
        output / "b" / "bundle",
        data=bundle.paths["data"],
        splits=bundle.paths["splits"],
        sources=bundle.paths["sources"],
        model=json_bytes(model_b),
        predictions=[{"row_id": r, "predicted_label": v} for r, v in zip(ids, labels, strict=True)],
        manifest=changed,
        measurement={
            "timings": [
                {
                    "name": "probe_revision_test_replay",
                    "unit": "seconds",
                    "device": "cpu",
                    "condition": "warm",
                    "value": seconds,
                    "sample_count": len(ids),
                    "batch_size": len(ids),
                }
            ],
            "memory_bytes": None,
            "memory_unknown_reason": "not sampled",
        },
        selection={"criterion": "predeclared synthetic rollout probe", "selected_method": "rules"},
    )
    expected: dict[str, Any] = {"probe": probe}
    for key in ("a", "b"):
        context = output / key
        digest = file_sha256(context / "bundle" / "manifest.json")
        loaded = load_trusted_local_classifier(context / "bundle", digest)
        expected[key] = {
            "predicted_label": predict_documents(loaded, [probe])[0],
            "bundle_sha256": digest,
            "model_id": loaded.bundle.manifest["model"]["id"],
            "preprocessing_version": loaded.bundle.manifest["preprocessing"]["version"],
        }
        (context / "service.json").write_bytes(
            json_bytes(
                {
                    "bundle_root": "/runtime/bundle",
                    "expected_manifest_sha256": digest,
                }
            )
        )
    (output / "expect.json").write_bytes(json_bytes(expected))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rules_bundle", type=Path)
    parser.add_argument("new_output", type=Path)
    parser.add_argument("probe")
    parser.add_argument("b_label")
    args = parser.parse_args()
    prepare(args.rules_bundle, args.new_output, args.probe, args.b_label)
