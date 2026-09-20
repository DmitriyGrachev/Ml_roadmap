import asyncio

import pytest
from fastapi.testclient import TestClient

from support_api.app import create_app
from support_api.provider_status import ProviderStatus


class CooperativeStatusProvider:
    def __init__(self, name: str, starts: list[str]) -> None:
        self.name = name
        self.starts = starts

    async def fetch_status(self) -> ProviderStatus:
        self.starts.append(self.name)
        if self.name == "primary":
            await asyncio.sleep(0)
            assert self.starts == ["primary", "backup"]
        return ProviderStatus(provider=self.name, available=True)


class FailingStatusProvider:
    async def fetch_status(self) -> ProviderStatus:
        raise RuntimeError("status provider unavailable")


def test_async_status_endpoint_fans_out_and_preserves_provider_order() -> None:
    starts: list[str] = []
    providers = [
        CooperativeStatusProvider("primary", starts),
        CooperativeStatusProvider("backup", starts),
    ]
    client = TestClient(create_app(status_providers=providers))

    response = client.get("/provider-statuses")

    assert response.status_code == 200
    assert response.json() == [
        {"provider": "primary", "available": True},
        {"provider": "backup", "available": True},
    ]


def test_async_status_endpoint_returns_an_empty_list_without_providers() -> None:
    client = TestClient(create_app(status_providers=[]))

    response = client.get("/provider-statuses")

    assert response.status_code == 200
    assert response.json() == []


def test_async_status_endpoint_propagates_a_provider_error() -> None:
    client = TestClient(create_app(status_providers=[FailingStatusProvider()]))

    with pytest.raises(RuntimeError, match="status provider unavailable"):
        client.get("/provider-statuses")
