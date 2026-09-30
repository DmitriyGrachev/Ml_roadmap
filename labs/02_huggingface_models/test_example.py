"""Mechanical offline checks; these never establish pretrained-model quality."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

PACKAGE = "labs.02_huggingface_models"


def require_example() -> Any:
    assert Path(__file__).with_name("example.py").is_file(), "offline example is missing"
    return importlib.import_module(f"{PACKAGE}.example")


def test_offline_example_has_no_required_network_or_pretrained_quality_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("torch", reason="NOT_RUN: install the opt-in training group")
    pytest.importorskip("transformers", reason="NOT_RUN: install the opt-in training group")
    import socket

    def deny_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("offline example attempted network access")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    result = require_example().run_smoke(tmp_path / "smoke")
    assert result["evidence"] == "LOCAL_RANDOM_ENCODER_SMOKE_ONLY"
    assert result["pretrained_quality"] == "NOT_RUN"
    assert result["logits_shape"] == [2, 2]
    assert result["reload_max_abs_difference"] < 1e-6
    assert result["padding_tokens"] > 0
    assert result["finite_logits"] is True
    assert (tmp_path / "smoke" / "model.safetensors").is_file()
    assert not list(tmp_path.rglob("*.bin"))


def test_example_import_does_not_require_training_dependencies() -> None:
    # Imports stay lazy; this test must also run in the base environment.
    assert callable(require_example().run_smoke)
