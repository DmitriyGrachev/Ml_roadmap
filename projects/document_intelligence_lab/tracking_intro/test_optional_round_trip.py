"""Explicit integration gate: never replace real MLflow with a fake tracker."""

import os
import socket
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

import pytest

from ..artifacts import read_json


@pytest.fixture(autouse=True)
def deny_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Actual local integration must also keep optional SDK background code offline."""
    attempts: list[object] = []

    def denied(sock: socket.socket, address: object) -> None:
        attempts.append(address)
        raise AssertionError("network is forbidden in the local MLflow exercise")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    yield
    assert attempts == []


@pytest.mark.optional_live
@pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_MLFLOW") != "1", reason="NOT_RUN: explicit MLflow runtime gate"
)
def test_real_two_runs_flavor_and_restored_bundle(tmp_path: Path) -> None:
    import importlib

    import numpy as np

    from .demo import run_demo

    output = run_demo(tmp_path / "tracking")
    report = read_json(output / "tracking.json")
    assert report["status"] == "RUN"
    assert len(report["runs"]) == 2
    assert report["runs"][0]["run_id"] != report["runs"][1]["run_id"]
    assert report["runs"][0]["bundle_sha256"] != report["runs"][1]["bundle_sha256"]
    assert Path(report["restored_bundle"]).is_dir()
    mlflow = importlib.import_module("mlflow")
    loaded = mlflow.pyfunc.load_model(report["runs"][0]["model_uri"])
    assert list(loaded.predict(np.array(["small red circle object"]))) == ["circle"]


@pytest.mark.optional_live
@pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_MLFLOW") != "1", reason="NOT_RUN: explicit MLflow runtime gate"
)
def test_registry_rollback_loads_pinned_bytes_and_rejects_alias_drift(tmp_path: Path) -> None:
    from .demo import _mlflow, local_store, run_demo
    from .registry import run_lifecycle, verify_selected_version

    tracking = run_demo(tmp_path / "tracking")
    report = run_lifecycle(tracking, tmp_path / "lifecycle")
    assert [step["version"] for step in report["steps"]] == ["1", "2", "1"]
    first, promoted, rolled_back = report["steps"]
    assert first["bundle_sha256"] != promoted["bundle_sha256"]
    assert first["model_sha256"] == rolled_back["model_sha256"]
    assert first["flavor_sha256"] == rolled_back["flavor_sha256"]
    assert first["predictions"] == ["circle", "square", "triangle", "circle", "square", "triangle"]
    assert rolled_back["predictions"] == first["predictions"]
    assert report["quality_defense"] == "REQUIRES_REVIEW"
    config = report["selected"]
    # A new output on the same tracking store must preserve both independent lifecycles.
    second_output = tmp_path / "second-lifecycle"
    run_lifecycle(tracking, second_output)
    second_config = read_json(second_output / "registry.json")["selected"]
    assert second_config["model_name"] != config["model_name"]
    for selected_config, replay_output in (
        (config, tmp_path / "first-lifecycle-replay"),
        (second_config, tmp_path / "second-lifecycle-replay"),
    ):
        replay = verify_selected_version(
            **selected_config, output=replay_output, trusted_local_artifact=True
        )
        assert replay["version"] == "1"
        assert replay["run_id"] == first["run_id"]
        assert replay["model_sha256"] == first["model_sha256"]
        assert replay["predictions"] == first["predictions"]
    with pytest.raises(ValueError, match="version"):
        verify_selected_version(
            **{**config, "expected_version": "2"},
            output=tmp_path / "wrong-version",
            trusted_local_artifact=True,
        )
    with pytest.raises(ValueError, match="flavor"):
        verify_selected_version(
            **{**config, "expected_flavor_sha256": "0" * 64},
            output=tmp_path / "wrong-flavor",
            trusted_local_artifact=True,
        )
    with pytest.raises(ValueError, match="trusted"):
        verify_selected_version(**config, output=tmp_path / "untrusted")
    uri, _ = local_store(Path(config["database"]), Path(config["artifact_root"]))
    client = _mlflow().MlflowClient(tracking_uri=uri, registry_uri=uri)
    remote = client.create_model_version(
        config["model_name"],
        source="https://example.invalid/model",
        run_id=config["expected_run_id"],
        tags={"bundle_sha256": config["expected_manifest_sha256"]},
    )
    client.set_registered_model_alias(config["model_name"], "remote-probe", remote.version)
    with pytest.raises(ValueError, match="local artifact root"):
        verify_selected_version(
            **{**config, "alias": "remote-probe", "expected_version": str(remote.version)},
            output=tmp_path / "remote",
            trusted_local_artifact=True,
        )
    assert not (tmp_path / "remote").exists()
    # Metadata pins still agree: independently altered bytes must also be rejected.
    selected = client.get_model_version(config["model_name"], config["expected_version"])
    flavor_metadata = Path(url2pathname(urlsplit(selected.source).path)) / "MLmodel"
    original = flavor_metadata.read_bytes()
    try:
        flavor_metadata.write_bytes(original + b"\n# modified after registration\n")
        with pytest.raises(ValueError, match="flavor"):
            verify_selected_version(
                **config, output=tmp_path / "altered-flavor", trusted_local_artifact=True
            )
        assert not (tmp_path / "altered-flavor").exists()
    finally:
        flavor_metadata.write_bytes(original)
