"""Laboratory pytest runs are always offline; downloads require a separate CLI."""

from __future__ import annotations

import asyncio
import socket
from collections.abc import Iterator

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


@pytest.fixture(scope="module")
def preinitialized_sync_event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Prepare only asyncio's internal wakeup sockets before the offline guard.

    Force CPython's Windows fallback on every platform, so Linux checks exercise
    the same socketpair connection that ProactorEventLoop needs on Windows.
    Higher fixture scope constructs this disposable loop before the function-scoped
    offline guard. The consuming test must use it in exactly one asyncio.run call.
    No user/provider coroutine runs during this trusted loop-construction step.
    """
    calls = 0

    def windows_wakeup_pair() -> tuple[socket.socket, socket.socket]:
        nonlocal calls
        calls += 1
        first, second = vars(socket)["_fallback_socketpair"]()
        return first, second

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket, "socketpair", windows_wakeup_pair)
        loop = asyncio.new_event_loop()
    assert calls > 0, "asyncio must exercise the Windows wakeup socketpair fallback"
    try:
        yield loop
    finally:
        if not loop.is_closed():
            loop.close()
