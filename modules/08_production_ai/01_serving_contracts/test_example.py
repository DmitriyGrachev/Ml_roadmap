"""Check local startup, drain, validation and cleanup behavior."""

import pytest
from fastapi.testclient import TestClient

from .example import Lifecycle, create_app, main


def test_lifecycle_drains_readiness_but_preserves_liveness_and_releases_resources() -> None:
    state = Lifecycle()
    with TestClient(create_app(state)) as client:
        assert client.get("/ready").status_code == 200
        assert client.post("/labels", json={"item_id": "M-001"}).json()["release"] == "v1"
        assert client.post("/labels", json={"item_id": "../secret"}).status_code == 422
        assert client.post("/labels", json={"item_id": "M-001", "admin": True}).status_code == 422
        state.drain()
        assert client.get("/live").status_code == 200
        assert client.get("/ready").status_code == 503
        assert client.post("/labels", json={"item_id": "M-001"}).status_code == 503
    assert state.closed
    assert not state.ready


def test_example_is_repeatable(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    first = capsys.readouterr().out
    main()
    assert capsys.readouterr().out == first
