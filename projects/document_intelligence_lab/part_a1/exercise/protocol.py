"""Read-only acceptance for locally operator-trusted learner evidence.

This validates replay/integrity. The explanation, independence, model selection
and generalization claim still need a human defense; no score threshold grants it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact

from ...artifacts import file_sha256, load_trusted_local_classifier, read_json, verify_bundle
from ...contracts import nonempty, object_value

FIXTURES = Path(__file__).parent / "fixtures"
EXERCISE_ID = "document-a1-reproduction"
ANALYSIS_FIELDS = {
    "source_permission",
    "annotation_ambiguity",
    "selection_reason",
    "error_analysis",
    "changed_requirement",
}


def validate_reproduction(root: Path, *, trusted_local_artifact: bool = False) -> dict[str, Any]:
    """Validate both independently produced bundles against the fixed library study.

    Local sklearn evidence is executable serialization: the reviewing operator must
    explicitly trust its local producer. Never call this on an uploaded report.
    """
    report = object_value(read_json(root / "report.json"), "reproduction report")
    if (
        type(report.get("schema_version")) is not int
        or report["schema_version"] != 1
        or report.get("exercise_id") != EXERCISE_ID
    ):
        raise ValueError("unsupported reproduction report schema/exercise_id")
    analysis = object_value(report.get("analysis"), "analysis")
    if set(analysis) != ANALYSIS_FIELDS:
        raise ValueError("analysis must address all defense prompts")
    for field, text in analysis.items():
        nonempty(text, field)
    references = object_value(report.get("bundles"), "bundles")
    if set(references) != {"rules", "tfidf-linear"}:
        raise ValueError("rules and tfidf-linear bundles are required")
    runs = []
    manifests = set()
    for method in ("rules", "tfidf-linear"):
        ref = object_value(references[method], "bundle reference")
        if set(ref) != {"path", "manifest_sha256"}:
            raise ValueError("bundle reference requires path and manifest_sha256")
        relative = nonempty(ref.get("path"), "bundle path")
        path = checked_artifact(root, relative + "/manifest.json", ref["manifest_sha256"])
        if path in manifests:
            raise ValueError("comparison bundles must be distinct")
        manifests.add(path)
        verified = verify_bundle(
            path.parent,
            expected_manifest_sha256=ref["manifest_sha256"],
            exercise_id=EXERCISE_ID,
            dataset_sha256=file_sha256(FIXTURES / "data.json"),
            split_sha256=file_sha256(FIXTURES / "splits.json"),
        )
        if file_sha256(verified.paths["sources"]) != file_sha256(FIXTURES / "sources.json"):
            raise ValueError("source/permission contract differs from fixed assignment")
        expected_format = "rules-json-v1" if method == "rules" else "sklearn-pickle-v1"
        if (
            verified.manifest["method"] != method
            or verified.manifest["model"]["format"] != expected_format
        ):
            raise ValueError("comparison method/model format mismatch")
        if verified.manifest["evidence_kind"] != "STUDENT_OFFLINE_REPRODUCTION":
            raise ValueError("teacher/other evidence cannot substitute for learner reproduction")
        load_trusted_local_classifier(
            path.parent, ref["manifest_sha256"], trusted_local_artifact=trusted_local_artifact
        )
        runs.append(verified)
    if runs[0].manifest["config"].get("seed") != runs[1].manifest["config"].get("seed"):
        raise ValueError("comparison methods require the same recorded seed")
    return {
        "mechanical_status": "VERIFIED",
        "learner_mastery": "REQUIRES_REVIEW",
        "methods": ["rules", "tfidf-linear"],
    }
