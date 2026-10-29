"""Mechanical artifact gate; provenance and interpretation still need human defense."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact

from ..artifacts import file_sha256, read_json, verify_bundle
from ..contracts import sha256_value
from .demo import STAGES, summarize

ANALYSIS = ("cold_warm", "timeout_cancellation", "rollback", "delayed_labels", "threshold_actions")


def required_evidence() -> Path:
    path = os.environ.get("ROADMAP_LIFECYCLE_EVIDENCE")
    if not path:
        raise NotImplementedError("Run learner TCP lifecycle; set ROADMAP_LIFECYCLE_EVIDENCE")
    return Path(path)


def validate_lifecycle(root: Path, *, learner: bool = True) -> dict[str, Any]:
    report = read_json(root / "lifecycle.json")
    expected_kind = "STUDENT_LOCAL_TCP" if learner else "AUTHOR_LOCAL_TCP_DEMO"
    if (
        type(report.get("schema_version")) is not int
        or report.get("schema_version") != 1
        or report.get("exercise_id") != "production-service-lifecycle"
        or report.get("evidence_kind") != expected_kind
        or report.get("transport") != "localhost TCP/uvicorn"
        or report.get("unit") != "seconds"
        or report.get("device") != "cpu"
    ):
        raise ValueError("wrong lifecycle identity/evidence kind/transport")
    if learner:
        if report.get("code_sha256") != file_sha256(Path(__file__).with_name("starter.py")):
            raise ValueError("learner source hash differs")
        analysis = report.get("analysis", {})
        if any(
            not isinstance(analysis.get(key), str) or not analysis[key].strip() for key in ANALYSIS
        ):
            raise ValueError("required analysis is missing")
    if report.get("run_status") != "COMPLETE":
        raise ValueError("lifecycle report is failed or incomplete")
    concurrency, count = report.get("concurrency"), report.get("requests_per_stage")
    if (
        type(count) is not int
        or not 2 <= count <= 200
        or type(concurrency) is not int
        or not 1 <= concurrency <= min(count, 16)
    ):
        raise ValueError("invalid bounded load config")
    bundles = report.get("bundles", {})
    if set(bundles) != {"A", "B"}:
        raise ValueError("saved A/B bundle references required")
    digests = {}
    identities = {}
    labels = {}
    for name, reference in bundles.items():
        manifest = checked_artifact(
            root, reference["path"] + "/manifest.json", reference["manifest_sha256"]
        )
        verified = verify_bundle(
            manifest.parent, expected_manifest_sha256=reference["manifest_sha256"]
        )
        digests[name] = verified.manifest_sha256
        identities[name] = {
            "bundle_sha256": verified.manifest_sha256,
            "model_id": verified.manifest["model"]["id"],
            "preprocessing_version": verified.manifest["preprocessing"]["version"],
        }
        labels[name] = verified.dataset.labels
    if digests["A"] == digests["B"]:
        raise ValueError("A/B must be different bundles")
    events = report.get("events", [])
    if [event.get("stage") for event in events] != list(STAGES):
        raise ValueError("missing restart/rejected/rollback stages")
    pids = []
    for event in events:
        if type(event.get("pid")) is not int or event["pid"] <= 0:
            raise ValueError("missing child PID")
        pids.append(event["pid"])
        summarize([{"outcome": "ok", "seconds": event.get("startup_seconds")}])
        if type(event.get("cleanup_exit_code")) is not int:
            raise ValueError("cleanup exit evidence missing")
        if event["stage"] == "rejected":
            if (
                event.get("startup_rejected") is not True
                or type(event.get("exit_code")) is not int
                or event["exit_code"] == 0
            ):
                raise ValueError("bad digest startup was not rejected")
            if event.get("bundle_name") not in bundles:
                raise ValueError("rejected stage must identify its saved bundle")
            sha256_value(event.get("bundle_sha256"), "configured rejected manifest digest")
            if event["bundle_sha256"] == digests[event["bundle_name"]]:
                raise ValueError("rejected digest must deliberately differ from saved bundle")
            log = event.get("startup_log", {})
            log_path = checked_artifact(root, log.get("path"), log.get("sha256"))
            log_text = log_path.read_text(encoding="utf-8")
            if (
                event.get("rejection_reason") != "manifest_digest_mismatch"
                or "manifest verification failed" not in log_text
                or "sha256" not in log_text
            ):
                raise ValueError("startup log does not show configured manifest digest rejection")
            continue
        name = "B" if event["stage"] == "B" else "A"
        expected = digests[name]
        first = event["first_request"]
        summarize([first])
        _prediction_identity(first, identities[name], labels[name])
        if (
            first["outcome"] != "ok"
            or first["status"] != 200
            or first["payload"]["bundle_sha256"] != expected
            or event["bundle_sha256"] != expected
        ):
            raise ValueError("first inference/bundle identity mismatch")
        rows = event["warm_requests"]
        if len(rows) != count or event["summary"] != summarize(rows):
            raise ValueError("warm summary differs from raw measurements")
        if any(
            r["outcome"] != "ok" or r["status"] != 200 or r["payload"] != first["payload"]
            for r in rows
        ):
            raise ValueError("warm request failed or changed identity/prediction")
        probes = event["fault_probes"]
        if (
            len(probes) != 2
            or probes[0]["outcome"] != "http_error"
            or probes[0]["status"] != 422
            or event["fault_summary"] != summarize(probes)
        ):
            raise ValueError("fault evidence/summary differs")
        for probe in probes:
            if probe["outcome"] == "ok":
                _prediction_identity(probe, identities[name], labels[name])
        summarize([{"outcome": "ok", "seconds": event["load_seconds"]}])
    # Fresh children normally have different PIDs; no reused process can claim restart.
    if len(set(pids)) != len(pids):
        raise ValueError("lifecycle did not use fresh children")
    first_payload = events[0]["first_request"]["payload"]
    if any(events[i]["first_request"]["payload"] != first_payload for i in (1, 4)):
        raise ValueError("restart/rollback differs")
    if events[2]["first_request"]["payload"]["predicted_label"] == first_payload["predicted_label"]:
        raise ValueError("A/B probe must exercise different inference")
    return {"mechanical_status": "VERIFIED", "learner_mastery": "REQUIRES_REVIEW"}


def _prediction_identity(
    row: dict[str, Any], identity: dict[str, Any], labels: tuple[str, ...]
) -> None:
    payload = row.get("payload")
    if (
        row.get("status") != 200
        or not isinstance(payload, dict)
        or set(payload) != {"predicted_label", *identity}
        or any(payload.get(key) != value for key, value in identity.items())
        or type(payload.get("preprocessing_version")) is not int
        or payload.get("predicted_label") not in labels
    ):
        raise ValueError("prediction response shape/model/preprocessing identity differs")
