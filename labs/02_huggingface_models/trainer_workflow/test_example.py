from importlib import import_module
from pathlib import Path

import pytest


def test_actual_local_trainer_checkpoint_selection_resume_and_reload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("accelerate", reason="uv sync --group trainer")
    import socket

    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", deny)
    e = import_module("labs.02_huggingface_models.trainer_workflow.example")
    result = e.run_example(tmp_path / "smoke")
    assert result["evidence"] == "RANDOM_LOCAL_MECHANICS_ONLY"
    assert result["global_step"] == 2
    assert result["resumed_step"] == 3
    assert result["best_metric"] == max(row["eval_accuracy"] for row in result["history"])
    assert result["model_identity"] == result["reload_identity"]
    assert result["reload_max_abs"] == 0.0
    assert (Path(result["best_checkpoint"]) / "trainer_state.json").is_file()
