"""The test harness must fail closed on accidental outbound connections."""

import os
import socket

import pytest


def test_laboratory_tests_cannot_connect_even_to_loopback() -> None:
    with pytest.raises(RuntimeError, match="Lab pytest is offline"):
        socket.create_connection(("127.0.0.1", 0), timeout=0.01)
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["HF_DATASETS_OFFLINE"] == "1"
