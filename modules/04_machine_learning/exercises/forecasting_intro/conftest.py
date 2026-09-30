"""All required forecasting tests run without network access."""

import socket
from collections.abc import Iterator
from unittest.mock import patch

import pytest


def blocked(*args: object, **kwargs: object) -> None:
    raise AssertionError("forecasting study must remain offline")


@pytest.fixture(scope="module", autouse=True)
def offline() -> Iterator[None]:
    with (
        patch.object(socket.socket, "connect", blocked),
        patch.object(socket.socket, "connect_ex", blocked),
        patch.object(socket, "create_connection", blocked),
    ):
        yield
