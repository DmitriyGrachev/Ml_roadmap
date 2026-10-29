"""The test harness must fail closed on accidental outbound connections."""

import asyncio
import os
import socket

import pytest


def test_laboratory_tests_cannot_connect_even_to_loopback() -> None:
    with pytest.raises(RuntimeError, match="Lab pytest is offline"):
        socket.create_connection(("127.0.0.1", 0), timeout=0.01)
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["HF_DATASETS_OFFLINE"] == "1"


def test_windows_wakeup_pair_supports_sync_runner_under_offline_guard(
    preinitialized_sync_event_loop: asyncio.AbstractEventLoop,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows fallback initializes before the guard; body errors still close the loop."""
    original_factory = asyncio.events.new_event_loop

    async def fail_after_wakeup() -> None:
        await asyncio.sleep(0)
        raise ValueError("observed coroutine body")

    with monkeypatch.context() as patch:
        patch.setattr(asyncio.events, "new_event_loop", lambda: preinitialized_sync_event_loop)
        with pytest.raises(ValueError, match="observed coroutine body"):
            asyncio.run(fail_after_wakeup())
    assert preinitialized_sync_event_loop.is_closed()
    assert asyncio.events.new_event_loop is original_factory


@pytest.mark.parametrize("method", ["create_connection", "connect", "connect_ex"])
@pytest.mark.parametrize("host", ["127.0.0.1", "203.0.113.1"])
def test_preinitialized_wakeup_does_not_permit_ordinary_connections(
    method: str,
    host: str,
) -> None:
    with socket.socket() as connection:
        operation = (
            socket.create_connection
            if method == "create_connection"
            else getattr(connection, method)
        )
        with pytest.raises(RuntimeError, match="Lab pytest is offline"):
            operation((host, 1))
