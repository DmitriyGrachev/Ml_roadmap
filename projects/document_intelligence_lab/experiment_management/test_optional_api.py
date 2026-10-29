"""One explicit four-trial CPU smoke; never required by default or learner credit."""

import os
import socket
from pathlib import Path

import pytest

from ..artifacts import json_bytes, read_json


@pytest.mark.optional_live
@pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_EXPERIMENTS") != "1",
    reason="NOT_RUN: set ROADMAP_RUN_EXPERIMENTS=1",
)
def test_actual_optuna_mlflow_search_and_model_reload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from .demo import run_demo
    from .evidence import validate_experiment

    attempts: list[object] = []

    def denied(sock: socket.socket, address: object) -> None:
        attempts.append(address)
        raise AssertionError("experiment smoke must stay offline")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    output = run_demo(tmp_path / "search")
    assert validate_experiment(output, learner=False, trusted_local_artifact=True) == {
        "mechanical_status": "VERIFIED",
        "learner_mastery": "REQUIRES_REVIEW",
    }
    saved = read_json(output / "experiment.json")
    assert len(saved["trials"]) == 4
    assert len({row["run_id"] for row in saved["trials"]}) == 4
    assert saved["versions"]["optuna"]
    assert saved["versions"]["mlflow"]
    with pytest.raises(ValueError, match="identity/evidence"):
        validate_experiment(output, trusted_local_artifact=True)
    with pytest.raises(ValueError, match="trusted"):
        validate_experiment(output, learner=False)
    with pytest.raises(FileExistsError):
        run_demo(output)
    # Change local store metadata independently of JSON: verifier must use real SDK state.
    from .runtime import libraries, local_paths

    mlflow, _ = libraries()
    _, _, uri, _ = local_paths(output)
    client = mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)
    target = saved["trials"][0]
    client.log_metric(target["run_id"], "dev_macro_f1", -0.25)
    with pytest.raises(ValueError, match="MLflow metric"):
        validate_experiment(output, learner=False, trusted_local_artifact=True)
    client.log_metric(target["run_id"], "dev_macro_f1", target["value"])
    saved["model_sha256"] = "0" * 64
    (output / "experiment.json").write_bytes(json_bytes(saved))
    with pytest.raises(ValueError, match="model flavor digest"):
        validate_experiment(output, learner=False, trusted_local_artifact=True)
    assert attempts == []
