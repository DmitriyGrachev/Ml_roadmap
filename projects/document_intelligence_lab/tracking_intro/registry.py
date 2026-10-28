"""Explicit local registry promotion/rollback with pinned bytes and real inference.

This is a teaching continuation, not a deployment controller or a pickle sandbox.
Protect the selected SQLite, artifact root and operator configuration from writers.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import url2pathname
from uuid import uuid4

from ..artifacts import (
    file_sha256,
    json_bytes,
    load_trusted_local_classifier,
    predict_documents,
    read_json,
)
from ..contracts import normalize_document
from .demo import _mlflow, local_store, require_local_artifact_uri, restore_run_new


def flavor_digest(root: Path) -> str:
    """Pin every flavor file and relative name; refuse links outside the trust boundary."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError("flavor must be a local directory")
    files = sorted(root.rglob("*"))
    if any(
        path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) for path in files
    ):
        raise ValueError("flavor links are unsupported")
    inventory = {
        path.relative_to(root).as_posix(): file_sha256(path) for path in files if path.is_file()
    }
    if "MLmodel" not in inventory or "model.pkl" not in inventory:
        raise ValueError("flavor requires MLmodel and fitted model.pkl")
    return hashlib.sha256(json_bytes(inventory)).hexdigest()


def _verify_version(
    *,
    database: str,
    artifact_root: str,
    model_name: str,
    expected_version: str,
    expected_run_id: str,
    expected_manifest_sha256: str,
    expected_flavor_sha256: str,
    output: Path,
    trusted_local_artifact: bool,
) -> dict[str, Any]:
    if trusted_local_artifact is not True:
        raise ValueError("registry flavor requires an explicitly trusted local artifact")
    uri, _ = local_store(Path(database), Path(artifact_root))
    mlflow = _mlflow()
    client = mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)
    version = client.get_model_version(model_name, expected_version)
    if version.run_id != expected_run_id or version.tags.get("bundle_sha256") != (
        expected_manifest_sha256
    ):
        raise ValueError("registry version/run/bundle identity mismatch")
    require_local_artifact_uri(version.source, Path(artifact_root))
    flavor = Path(url2pathname(urlsplit(version.source).path))
    if version.tags.get("flavor_sha256") != expected_flavor_sha256 or flavor_digest(flavor) != (
        expected_flavor_sha256
    ):
        raise ValueError("registry flavor digest mismatch")
    restored = restore_run_new(
        expected_run_id,
        output,
        expected_manifest_sha256=expected_manifest_sha256,
        database=Path(database),
        artifact_root=Path(artifact_root),
        trusted_local_artifact=True,
    )
    classifier = load_trusted_local_classifier(
        restored, expected_manifest_sha256, trusted_local_artifact=True
    )
    texts = [classifier.bundle.dataset.by_id[row].text for row in classifier.bundle.splits["test"]]
    expected = predict_documents(classifier, texts)
    # URI was contained and all flavor bytes pinned BEFORE executable deserialization.
    loaded = mlflow.sklearn.load_model(str(flavor))
    actual = [str(value) for value in loaded.predict([normalize_document(text) for text in texts])]
    if actual != expected:
        raise ValueError("selected registry flavor prediction mismatch")
    return {
        "version": str(version.version),
        "run_id": version.run_id,
        "bundle_sha256": expected_manifest_sha256,
        "flavor_sha256": expected_flavor_sha256,
        "model_sha256": file_sha256(classifier.bundle.paths["model"]),
        "restored_bundle": str(restored),
        "predictions": actual,
        "test_row_ids": list(classifier.bundle.splits["test"]),
        "metrics": read_json(classifier.bundle.paths["metrics"]),
        "dataset_sha256": classifier.bundle.manifest["dataset_sha256"],
        "split_sha256": classifier.bundle.manifest["split_sha256"],
        "config": classifier.bundle.manifest["config"],
        "code": classifier.bundle.manifest["code"],
        "runtime": classifier.bundle.manifest["versions"],
    }


def verify_selected_version(
    *,
    database: str,
    artifact_root: str,
    model_name: str,
    alias: str,
    expected_version: str,
    expected_run_id: str,
    expected_manifest_sha256: str,
    expected_flavor_sha256: str,
    output: Path,
    trusted_local_artifact: bool = False,
) -> dict[str, Any]:
    """Resolve a persisted alias, require operator pins, restore and predict anew."""
    uri, _ = local_store(Path(database), Path(artifact_root))
    mlflow = _mlflow()
    client = mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)
    selected = client.get_model_version_by_alias(model_name, alias)
    if str(selected.version) != expected_version:
        raise ValueError("persisted alias version differs from operator configuration")
    return _verify_version(
        database=database,
        artifact_root=artifact_root,
        model_name=model_name,
        expected_version=expected_version,
        expected_run_id=expected_run_id,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_flavor_sha256=expected_flavor_sha256,
        output=output,
        trusted_local_artifact=trusted_local_artifact,
    )


def run_lifecycle(tracking: Path, output: Path) -> dict[str, Any]:
    """Register two real A1 flavors, validate/promote 1→2, then restore/rollback 2→1."""
    if output.exists():
        raise FileExistsError(f"registry output already exists: {output}")
    tracking, output = tracking.resolve(), output.resolve()
    database, artifact_root = tracking / "store" / "runs.sqlite", tracking / "store" / "artifacts"
    uri, _ = local_store(database, artifact_root)
    mlflow = _mlflow()
    client = mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)
    runs = read_json(tracking / "tracking.json")["runs"]
    if len(runs) != 2 or runs[0]["run_id"] == runs[1]["run_id"]:
        raise ValueError("select two distinct completed teacher runs")
    model_name = f"document-cpu-{runs[0]['run_id']}-{uuid4().hex}"
    client.create_registered_model(model_name)
    pins = []
    for run in runs:
        require_local_artifact_uri(client.get_run(run["run_id"]).info.artifact_uri, artifact_root)
        # MLflow 3 logged-model ID is distinct from registry version and experiment run ID.
        logged = client.get_logged_model(run["model_uri"].removeprefix("models:/"))
        if logged.source_run_id != run["run_id"]:
            raise ValueError("logged model differs from selected run")
        require_local_artifact_uri(logged.artifact_location, artifact_root)
        digest = flavor_digest(Path(url2pathname(urlsplit(logged.artifact_location).path)))
        version = client.create_model_version(
            model_name,
            source=logged.artifact_location,
            run_id=run["run_id"],
            tags={"bundle_sha256": run["bundle_sha256"], "flavor_sha256": digest},
        )
        pins.append(
            {
                "database": str(database),
                "artifact_root": str(artifact_root),
                "model_name": model_name,
                "expected_version": str(version.version),
                "expected_run_id": run["run_id"],
                "expected_manifest_sha256": run["bundle_sha256"],
                "expected_flavor_sha256": digest,
            }
        )
    output.mkdir(parents=True, exist_ok=False)
    steps = []
    for action, pin in zip(
        ("initial", "promotion", "rollback"), (pins[0], pins[1], pins[0]), strict=True
    ):
        checked = _verify_version(
            **pin, output=output / f"{action}-preflight", trusted_local_artifact=True
        )
        client.set_registered_model_alias(model_name, "champion", pin["expected_version"])
        selected = client.get_model_version_by_alias(model_name, "champion")
        if str(selected.version) != checked["version"] or selected.run_id != checked["run_id"]:
            raise ValueError("persisted alias differs after explicit promotion")
        steps.append({"action": action, "alias": "champion", **checked})
    selected_config = {**pins[0], "alias": "champion"}
    replay = verify_selected_version(
        **selected_config, output=output / "rollback-replay", trusted_local_artifact=True
    )
    report = {
        "status": "RUN",
        "evidence_kind": "AUTHOR_SYNTHETIC_MLFLOW_REGISTRY_SMOKE_ONLY",
        "mlflow_version": mlflow.__version__,
        "registry_source_sha256": file_sha256(Path(__file__)),
        "steps": steps,
        "selected": selected_config,
        "rollback_replay": replay,
        "quality_defense": "REQUIRES_REVIEW",
        "hosted_deployment": "NOT_RUN",
    }
    (output / "registry.json").write_bytes(json_bytes(report))
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking", type=Path)
    parser.add_argument("--selected-config", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if (args.tracking is None) == (args.selected_config is None):
        parser.error("select exactly one of --tracking or --selected-config")
    if args.tracking is not None:
        run_lifecycle(args.tracking, args.output)
    else:
        # Operator selected protected local config; never expose this through a request body.
        config = read_json(args.selected_config)["selected"]
        report = verify_selected_version(**config, output=args.output, trusted_local_artifact=True)
        (args.output / "restart-verification.json").write_bytes(json_bytes(report))
    print(args.output)


if __name__ == "__main__":
    main()
