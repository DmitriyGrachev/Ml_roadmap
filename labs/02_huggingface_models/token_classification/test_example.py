from importlib import import_module
from pathlib import Path

import pytest


def test_real_token_collation_loss_and_reload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("transformers", reason="uv sync --group trainer")
    import socket

    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", deny)
    e = import_module("labs.02_huggingface_models.token_classification.example")
    result = e.run_example(tmp_path / "smoke")
    assert result["evidence"] == "RANDOM_LOCAL_MECHANICS_ONLY"
    assert result["finite_loss"]
    assert result["reload_max_abs"] == 0.0
    assert result["labels"][0] == [-100, 1, -100, 0, 3, 0, -100]
    assert result["padding_ignored"]
