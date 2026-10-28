"""Narrow classification teacher releases; no registry, automatic gate or index loader."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from projects.document_intelligence_lab.artifacts import (
    VerifiedBundle,
    file_sha256,
    json_bytes,
    read_json,
    verify_bundle,
)
from roadmap_tools.experiment_evidence import checked_artifact


def _identity(bundle: VerifiedBundle) -> dict[str, Any]:
    manifest = bundle.manifest
    return {
        "model_sha256": file_sha256(bundle.paths["model"]),
        "data_sha256": manifest["dataset_sha256"],
        "split_sha256": manifest["split_sha256"],
        "sources_sha256": file_sha256(bundle.paths["sources"]),
        "preprocessing": manifest["preprocessing"],
        "code": manifest["code"],
        "config": manifest["config"],
        "labels": manifest["labels"],
        "versions": manifest["versions"],
    }


def _copy_bundle(bundle: VerifiedBundle, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for source in (bundle.root / "manifest.json", *bundle.paths.values()):
        target = destination / source.relative_to(bundle.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def write_release_new(bundle_root: Path, output: Path, *, expected_bundle_sha256: str) -> Path:
    """Copy verified bytes into a NEW release; operator records returned digest externally."""
    if output.exists():
        raise FileExistsError(f"release already exists: {output}")
    bundle = verify_bundle(bundle_root, expected_manifest_sha256=expected_bundle_sha256)
    manifest = {
        "schema_version": 1,
        "evidence_kind": "AUTHOR_CLASSIFICATION_RELEASE_SMOKE_ONLY",
        "bundle_path": "bundle",
        "bundle_sha256": expected_bundle_sha256,
        "identity": _identity(bundle),
        "lifecycle_source_sha256": file_sha256(Path(__file__)),
        "index": None,
    }
    output.mkdir(parents=True, exist_ok=False)
    _copy_bundle(bundle, output / "bundle")
    path = output / "release.json"
    path.write_bytes(json_bytes(manifest))
    verify_release(output, expected_release_sha256=file_sha256(path))
    return path


def verify_release(root: Path, *, expected_release_sha256: str) -> dict[str, Any]:
    """Check external release identity, actual complete bundle bytes and identity binding."""
    path = checked_artifact(root, "release.json", expected_release_sha256)
    manifest = read_json(path)
    if (
        not isinstance(manifest, dict)
        or set(manifest)
        != {
            "schema_version",
            "evidence_kind",
            "bundle_path",
            "bundle_sha256",
            "identity",
            "lifecycle_source_sha256",
            "index",
        }
        or type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != 1
        or manifest["bundle_path"] != "bundle"
        or manifest["evidence_kind"] != "AUTHOR_CLASSIFICATION_RELEASE_SMOKE_ONLY"
        or manifest["index"] is not None
    ):
        raise ValueError("unsupported classification release schema/index")
    source_digest = manifest["lifecycle_source_sha256"]
    if (
        not isinstance(source_digest, str)
        or len(source_digest) != 64
        or any(char not in "0123456789abcdef" for char in source_digest)
    ):
        raise ValueError("invalid lifecycle source identity")
    # Root containment and symlink checks are delegated to the existing checksum boundary.
    checked_artifact(root, "bundle/manifest.json", manifest["bundle_sha256"])
    bundle = verify_bundle(root / "bundle", expected_manifest_sha256=manifest["bundle_sha256"])
    if json_bytes(manifest["identity"]) != json_bytes(_identity(bundle)):
        raise ValueError("release identity differs from actual bundle")
    return manifest


def restore_release_new(
    release_root: Path,
    output: Path,
    *,
    expected_release_sha256: str,
    trusted_local_artifact: bool = False,
) -> Path:
    """Verify and copy into NEW storage, then actually start selected service and predict.

    No active pointer changes here. Human selection of the fixed expected release
    digest is the promotion/rollback decision; pickle trust remains separate.
    """
    if output.exists():
        raise FileExistsError(f"restore already exists: {output}")
    manifest = verify_release(release_root, expected_release_sha256=expected_release_sha256)
    bundle = verify_bundle(
        release_root / "bundle", expected_manifest_sha256=manifest["bundle_sha256"]
    )
    if bundle.manifest["model"]["format"] != "rules-json-v1" and not trusted_local_artifact:
        raise ValueError("pickle requires an explicitly trusted local artifact")
    from fastapi.testclient import TestClient

    from projects.document_intelligence_lab.service.app import create_app

    output.mkdir(parents=True, exist_ok=False)
    _copy_bundle(bundle, output / "bundle")
    (output / "release.json").write_bytes((release_root / "release.json").read_bytes())
    verify_release(output, expected_release_sha256=expected_release_sha256)
    with TestClient(
        create_app(
            output / "bundle",
            manifest["bundle_sha256"],
            trusted_local_artifact=trusted_local_artifact,
        )
    ) as client:
        ready = client.get("/ready")
        ready.raise_for_status()
        response = client.post("/predict", json={"text": "triangle"})
        response.raise_for_status()
        probe = response.json()
        if probe["bundle_sha256"] != manifest["bundle_sha256"]:
            raise ValueError("recovered service bundle identity mismatch")
    (output / "restart.json").write_bytes(
        json_bytes(
            {
                "evidence_kind": "AUTHOR_IN_PROCESS_RESTART_SMOKE_ONLY",
                "release_sha256": expected_release_sha256,
                "ready": True,
                "probe": probe,
                "network_server": "NOT_RUN",
            }
        )
    )
    return output
