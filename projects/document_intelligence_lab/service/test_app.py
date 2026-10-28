"""Teacher API tests: all artifacts are generated in test-owned storage."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ..artifacts import file_sha256, json_bytes, load_trusted_local_classifier, predict_documents
from ..part_a1.demo import run_demo


@pytest.fixture(autouse=True)
def reject_external_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    real_connect = socket.socket.connect

    def blocked(connection: socket.socket, address: Any) -> None:
        # Windows asyncio uses loopback socketpair internally for its event loop.
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return real_connect(connection, address)
        raise AssertionError("offline service checks must not open external sockets")

    monkeypatch.setattr(socket.socket, "connect", blocked)


@pytest.fixture(scope="module")
def teacher(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return run_demo(tmp_path_factory.mktemp("service") / "teacher")


def test_prediction_matches_bundle_and_close_clears_readiness(teacher: Path) -> None:
    from .app import create_app

    root = teacher / "rules"
    digest = file_sha256(root / "manifest.json")
    classifier = load_trusted_local_classifier(root, digest)
    app = create_app(root, digest)
    with TestClient(app) as client:
        assert client.get("/ready").json() == {"ready": True, "bundle_sha256": digest}
        for text, expected in [("  SQUARE\n", "square"), ("triangle", "circle")]:
            response = client.post("/predict", json={"text": text})
            assert response.status_code == 200
            assert response.json() == {
                "predicted_label": expected,
                "model_id": "a1-rules",
                "preprocessing_version": 1,
                "bundle_sha256": digest,
            }
            assert predict_documents(classifier, [text]) == [expected]
    with TestClient(app) as restarted:
        assert (
            restarted.post("/predict", json={"text": "square"}).json()["predicted_label"]
            == "square"
        )
    assert app.state.classifier is None


def test_no_lifespan_is_not_ready_and_factory_requires_config(
    teacher: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from .app import create_app, factory

    root = teacher / "rules"
    client = TestClient(create_app(root, file_sha256(root / "manifest.json")))
    try:
        assert client.get("/ready").status_code == 503
        assert client.post("/predict", json={"text": "circle"}).status_code == 503
    finally:
        client.close()
    monkeypatch.delenv("ROADMAP_SERVICE_CONFIG", raising=False)
    with pytest.raises(ValueError, match="ROADMAP_SERVICE_CONFIG"):
        factory()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": ""},
        {"text": " \n"},
        {"text": "x" * 10001},
        {"text": 1},
        {"text": "circle", "bundle_root": "C:/untrusted"},
        {"text": "circle", "expected_manifest_sha256": "0" * 64},
        {"text": "circle", "url": "https://example.com/model.pkl"},
        {"text": "circle", "trusted_local_artifact": True},
        {"text": "circle", "label": "circle"},
        {"texts": ["circle"]},
    ],
)
def test_request_cannot_change_model_or_bypass_text_bounds(teacher: Path, payload: Any) -> None:
    from .app import create_app

    root = teacher / "rules"
    with TestClient(create_app(root, file_sha256(root / "manifest.json"))) as client:
        assert client.post("/predict", json=payload).status_code == 422
        assert client.post("/predict", files={"model": ("model.pkl", b"pickle")}).status_code == 422


def test_load_once_at_startup_and_not_before_lifespan(teacher: Path, tmp_path: Path) -> None:
    import shutil

    from .app import create_app

    root = tmp_path / "copy"
    shutil.copytree(teacher / "rules", root)
    app = create_app(root, file_sha256(root / "manifest.json"))
    assert app.state.classifier is None
    with TestClient(app) as client:
        (root / "model.json").write_text("tampered after startup", encoding="utf-8")
        assert (
            client.post("/predict", json={"text": "square"}).json()["predicted_label"] == "square"
        )
    with pytest.raises(ValueError, match=r"sha256|size_bytes"), TestClient(app):
        pass


@pytest.mark.parametrize("failure", ["absent", "tampered", "schema", "preprocessing", "labels"])
def test_invalid_bundle_fails_startup_without_fallback(
    teacher: Path, tmp_path: Path, failure: str
) -> None:
    import shutil

    from .app import create_app

    root = tmp_path / "bundle"
    shutil.copytree(teacher / "rules", root)
    digest = file_sha256(root / "manifest.json")
    if failure == "absent":
        root = tmp_path / "missing"
    elif failure == "tampered":
        (root / "model.json").write_bytes(b"{}")
    else:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if failure == "schema":
            manifest["schema_version"] = 999
        elif failure == "preprocessing":
            manifest["preprocessing"]["version"] = 999
        else:
            manifest["labels"] = list(reversed(manifest["labels"]))
        (root / "manifest.json").write_bytes(json_bytes(manifest))
        digest = file_sha256(root / "manifest.json")
    with (
        pytest.raises(ValueError, match=r"manifest|sha256|schema|preprocessing|label|size_bytes"),
        TestClient(create_app(root, digest)),
    ):
        pass


def test_sklearn_requires_explicit_operator_trust(teacher: Path) -> None:
    from .app import create_app

    root = teacher / "tfidf-linear"
    digest = file_sha256(root / "manifest.json")
    with pytest.raises(ValueError, match="trusted"), TestClient(create_app(root, digest)):
        pass
    with TestClient(create_app(root, digest, trusted_local_artifact=True)) as client:
        assert (
            client.post("/predict", json={"text": "triangle"}).json()["predicted_label"]
            == "triangle"
        )


def test_config_launch_uses_exact_operator_paths(teacher: Path, tmp_path: Path) -> None:
    from .app import create_app_from_config

    root = teacher / "rules"
    config = tmp_path / "service.json"
    config.write_bytes(
        json_bytes(
            {
                "bundle_root": str(root),
                "expected_manifest_sha256": file_sha256(root / "manifest.json"),
            }
        )
    )
    with TestClient(create_app_from_config(config)) as client:
        assert (
            client.post("/predict", json={"text": "square"}).json()["predicted_label"] == "square"
        )
    config.write_bytes(
        json_bytes({"bundle_root": "relative", "expected_manifest_sha256": "0" * 64})
    )
    with pytest.raises(ValueError, match="absolute"):
        create_app_from_config(config)
    config.write_bytes(
        json_bytes({"bundle_root": "//server/share/bundle", "expected_manifest_sha256": "0" * 64})
    )
    with pytest.raises(ValueError, match="local"):
        create_app_from_config(config)
