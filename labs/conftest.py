"""Laboratory pytest runs are always offline; downloads require a separate CLI."""

from __future__ import annotations

import socket

import pytest


@pytest.fixture(autouse=True)
def offline_laboratories(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turn an accidental model download during a lab test into a visible failure."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("HF_DATASETS_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setenv("HF_HUB_DISABLE_TELEMETRY", "1")

    def deny(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Lab pytest is offline; use the explicit download command separately")

    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
