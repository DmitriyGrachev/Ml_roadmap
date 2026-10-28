"""Two actual teacher runs, local SQLite, artifact restore and sklearn flavor.

MLflow is lazy and optional. This command never installs or starts a server.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import url2pathname

from ..artifacts import (
    file_sha256,
    json_bytes,
    load_trusted_local_classifier,
    predict_documents,
    read_json,
)
from ..contracts import normalize_document


def local_store(database: Path, artifact_root: Path) -> tuple[str, str]:
    """Construct local-only URIs; never accept a remote tracking endpoint."""
    if (
        not database.is_absolute()
        or not artifact_root.is_absolute()
        or database.as_posix().startswith("//")
        or artifact_root.as_posix().startswith("//")
    ):
        raise ValueError("database and artifact_root must be absolute local paths")
    if database == artifact_root or database.suffix != ".sqlite":
        raise ValueError("select a .sqlite metadata file and a separate artifact directory")
    return "sqlite:///" + database.as_posix(), artifact_root.as_uri()


def _mlflow() -> Any:
    # This lesson is strictly local, including SDK background behavior.
    os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
    try:
        return importlib.import_module("mlflow")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "NOT_RUN: MLflow runtime missing. Select the separately approved tracking environment; "
            "this command does not install packages."
        ) from exc


def require_local_artifact_uri(uri: str, artifact_root: Path) -> None:
    """Local SQLite metadata does not by itself guarantee local artifact bytes."""
    parsed = urlsplit(uri)
    path = Path(url2pathname(parsed.path))
    if (
        parsed.scheme != "file"
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or not path.is_absolute()
        or not path.resolve().is_relative_to(artifact_root.resolve())
    ):
        raise ValueError("run artifact URI must stay within the selected local artifact root")


def track_bundle(
    bundle_root: Path,
    expected_manifest_sha256: str,
    *,
    database: Path,
    artifact_root: Path,
    experiment_name: str,
    trusted_local_artifact: bool = False,
) -> dict[str, str]:
    """Log verified bundle bytes and an explicitly trusted sklearn model flavor.

    Flavor signature is NORMALIZED strings; the full raw-text preprocessing and
    identity remain in the bundle. Registry/promotion is a separate continuation.
    """
    tracking_uri, artifact_uri = local_store(database, artifact_root)
    mlflow = _mlflow()
    import numpy as np

    classifier = load_trusted_local_classifier(
        bundle_root, expected_manifest_sha256, trusted_local_artifact=trusted_local_artifact
    )
    if classifier.bundle.manifest["model"]["format"] != "sklearn-pickle-v1":
        raise ValueError("tracking introduction requires a trusted teacher sklearn pipeline")
    if not experiment_name.strip():
        raise ValueError("experiment_name must be nonempty")
    database.parent.mkdir(parents=True, exist_ok=True)
    artifact_root.mkdir(parents=True, exist_ok=True)
    client = mlflow.MlflowClient(tracking_uri=tracking_uri, registry_uri=tracking_uri)
    existing = client.get_experiment_by_name(experiment_name)
    if existing is None:
        experiment_id = client.create_experiment(experiment_name, artifact_location=artifact_uri)
    else:
        if existing.artifact_location.rstrip("/") != artifact_uri.rstrip("/"):
            raise ValueError("existing experiment uses a different artifact location")
        experiment_id = existing.experiment_id
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_registry_uri(tracking_uri)
    manifest = classifier.bundle.manifest
    texts = [classifier.bundle.dataset.by_id[row].text for row in classifier.bundle.splits["test"]]
    normalized = [normalize_document(text) for text in texts]
    expected = predict_documents(classifier, texts)
    metrics = read_json(classifier.bundle.paths["metrics"])
    with mlflow.start_run(experiment_id=experiment_id, run_name=manifest["run_id"]) as run:
        require_local_artifact_uri(run.info.artifact_uri, artifact_root)
        mlflow.log_params(
            {
                "method": manifest["method"],
                "seed": manifest["config"]["seed"],
                "config_json": json.dumps(manifest["config"], sort_keys=True),
                "preprocessing_id": manifest["preprocessing"]["id"],
                "preprocessing_version": manifest["preprocessing"]["version"],
            }
        )
        mlflow.log_metrics({key: float(metrics[key]) for key in ("accuracy", "macro_f1", "count")})
        mlflow.set_tags(
            {
                "bundle_sha256": expected_manifest_sha256,
                "dataset_sha256": manifest["dataset_sha256"],
                "split_sha256": manifest["split_sha256"],
                "evidence_kind": manifest["evidence_kind"],
                "code_source_sha256": manifest["code"]["source_sha256"],
            }
        )
        # Explicit allowlist: never upload arbitrary neighboring/private files.
        mlflow.log_artifact(str(classifier.bundle.root / "manifest.json"), artifact_path="bundle")
        for path in classifier.bundle.paths.values():
            relative_parent = path.relative_to(classifier.bundle.root).parent
            destination = (Path("bundle") / relative_parent).as_posix()
            mlflow.log_artifact(str(path), artifact_path=destination)
        model_info = mlflow.sklearn.log_model(
            sk_model=classifier.model,
            name="normalized_document_pipeline",
            # A 1-D string tensor preserves sklearn's document sequence contract.
            # A column schema would convert input to a DataFrame whose iteration is column IDs.
            signature=mlflow.models.infer_signature(np.array(normalized), np.array(expected)),
            input_example=np.array(normalized[:1]),
            serialization_format="pickle",
            pip_requirements=[
                f"scikit-learn=={manifest['versions']['sklearn']}",
                f"numpy=={manifest['versions']['numpy']}",
                f"scipy=={manifest['versions']['scipy']}",
            ],
            metadata={
                "input_boundary": "unicode-whitespace-v1 normalized strings",
                "bundle_sha256": expected_manifest_sha256,
            },
        )
        loaded = mlflow.sklearn.load_model(model_info.model_uri)
        if list(loaded.predict(normalized)) != expected:
            raise ValueError("MLflow sklearn flavor reload prediction mismatch")
        return {
            "run_id": run.info.run_id,
            "bundle_sha256": expected_manifest_sha256,
            "model_uri": model_info.model_uri,
        }


def restore_run_new(
    run_id: str,
    output: Path,
    *,
    expected_manifest_sha256: str,
    database: Path,
    artifact_root: Path,
    trusted_local_artifact: bool = False,
) -> Path:
    """Recover local run bytes into a fresh directory, verify and replay inference."""
    if output.exists():
        raise FileExistsError(f"restore output already exists: {output}")
    uri, _ = local_store(database, artifact_root)
    mlflow = _mlflow()
    client = mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)
    require_local_artifact_uri(client.get_run(run_id).info.artifact_uri, artifact_root)
    output.mkdir(parents=True, exist_ok=False)
    restored = Path(
        mlflow.artifacts.download_artifacts(
            run_id=run_id,
            artifact_path="bundle",
            dst_path=str(output),
            tracking_uri=uri,
        )
    )
    load_trusted_local_classifier(
        restored, expected_manifest_sha256, trusted_local_artifact=trusted_local_artifact
    )
    return restored


def run_demo(output: Path) -> Path:
    if output.exists():
        raise FileExistsError(f"tracking output already exists: {output}")
    mlflow = _mlflow()  # Missing runtime leaves no generated directories or fake successful runs.
    from ..part_a1.demo import run_demo as run_a1

    output = output.resolve()
    database, artifacts = output / "store" / "runs.sqlite", output / "store" / "artifacts"
    output.mkdir(parents=True, exist_ok=False)
    runs = []
    for seed in (17, 29):
        teacher = run_a1(output / f"teacher-seed-{seed}", seed=seed)
        root = teacher / "tfidf-linear"
        runs.append(
            track_bundle(
                root,
                file_sha256(root / "manifest.json"),
                database=database,
                artifact_root=artifacts,
                experiment_name="document-cpu-teacher",
                trusted_local_artifact=True,
            )
        )
    restored = restore_run_new(
        runs[0]["run_id"],
        output / "restored-run-17",
        expected_manifest_sha256=runs[0]["bundle_sha256"],
        database=database,
        artifact_root=artifacts,
        trusted_local_artifact=True,
    )
    (output / "tracking.json").write_bytes(
        json_bytes(
            {
                "evidence_kind": "AUTHOR_SYNTHETIC_MLFLOW_SMOKE_ONLY",
                "status": "RUN",
                "mlflow_version": mlflow.__version__,
                "tracking_source_sha256": file_sha256(Path(__file__)),
                "telemetry": "DISABLED_BEFORE_IMPORT",
                "flavor_input": "1-D normalized string tensor; raw texts require bundle loader",
                "runs": runs,
                "restored_bundle": str(restored),
                "tracking_uri": local_store(database, artifacts)[0],
                "artifact_root": artifacts.as_uri(),
                "registry_promotion": "NOT_RUN",
                "quality_defense": "REQUIRES_REVIEW",
            }
        )
    )
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(run_demo(args.output))
    except RuntimeError as exc:
        parser.exit(status=2, message=f"{exc}\n")


if __name__ == "__main__":
    main()
