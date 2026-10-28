"""Offline author checks; these never award learner completion."""

from __future__ import annotations

import importlib
import shutil
import socket
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import httpx
import pytest

from projects.document_intelligence_lab.artifacts import (
    file_sha256,
    json_bytes,
    load_trusted_local_classifier,
    read_json,
)
from projects.document_intelligence_lab.part_a1.demo import run_demo

releases = importlib.import_module("labs.06_ml_lifecycle.releases")
demo = importlib.import_module("labs.06_ml_lifecycle.demo")
ORIGINAL_CONNECT = socket.socket.connect


@pytest.fixture(autouse=True)
def permit_eventloop_wakeup_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Windows asyncio needs numeric loopback; no HTTP network transport is allowed."""

    def connect(connection: socket.socket, address: Any) -> None:
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return ORIGINAL_CONNECT(connection, address)
        raise RuntimeError("R09 offline checks reject external sockets")

    def deny_http(*args: object, **kwargs: object) -> None:
        raise RuntimeError("R09 offline checks reject TCP HTTP transports")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", deny_http)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", deny_http)


def test_offline_guard_rejects_external_socket_and_tcp_http() -> None:
    with socket.socket() as connection, pytest.raises(RuntimeError, match="external"):
        connection.connect(("203.0.113.1", 443))
    with httpx.Client() as client, pytest.raises(RuntimeError, match="TCP HTTP"):
        client.get("http://127.0.0.1:1")


@pytest.fixture(scope="module")
def teacher(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return run_demo(tmp_path_factory.mktemp("r09") / "teacher") / "rules"


def test_release_copies_bytes_and_recovery_restarts_real_service(
    teacher: Path, tmp_path: Path
) -> None:
    manifest = releases.write_release_new(
        teacher, tmp_path / "release", expected_bundle_sha256=file_sha256(teacher / "manifest.json")
    )
    digest = file_sha256(manifest)
    original = releases.verify_release(manifest.parent, expected_release_sha256=digest)
    restored = releases.restore_release_new(
        manifest.parent, tmp_path / "restored", expected_release_sha256=digest
    )
    assert restored == tmp_path / "restored"
    assert file_sha256(restored / "bundle" / "manifest.json") == original["bundle_sha256"]
    report = read_json(restored / "restart.json")
    assert report["ready"] is True
    assert report["probe"]["predicted_label"] == "circle"
    assert report["probe"]["bundle_sha256"] == original["bundle_sha256"]


def test_release_identity_tamper_rejected_even_with_new_release_digest(
    teacher: Path, tmp_path: Path
) -> None:
    manifest = releases.write_release_new(
        teacher, tmp_path / "release", expected_bundle_sha256=file_sha256(teacher / "manifest.json")
    )
    payload = read_json(manifest)
    payload["identity"]["preprocessing"]["version"] = 99
    manifest.write_bytes(json_bytes(payload))
    with pytest.raises(ValueError, match="identity"):
        releases.verify_release(manifest.parent, expected_release_sha256=file_sha256(manifest))


def test_fixed_expected_digest_rejects_changed_release(teacher: Path, tmp_path: Path) -> None:
    manifest = releases.write_release_new(
        teacher, tmp_path / "release", expected_bundle_sha256=file_sha256(teacher / "manifest.json")
    )
    digest = file_sha256(manifest)
    manifest.write_bytes(manifest.read_bytes() + b" ")
    with pytest.raises(ValueError, match="sha256"):
        releases.verify_release(manifest.parent, expected_release_sha256=digest)


def test_missing_model_cannot_create_recovered_output(teacher: Path, tmp_path: Path) -> None:
    manifest = releases.write_release_new(
        teacher, tmp_path / "release", expected_bundle_sha256=file_sha256(teacher / "manifest.json")
    )
    digest = file_sha256(manifest)
    (manifest.parent / "bundle" / "model.json").unlink()
    with pytest.raises(ValueError, match="artifact"):
        releases.restore_release_new(
            manifest.parent, tmp_path / "restored", expected_release_sha256=digest
        )
    assert not (tmp_path / "restored").exists()


def test_release_and_restore_never_overwrite(teacher: Path, tmp_path: Path) -> None:
    manifest = releases.write_release_new(
        teacher, tmp_path / "release", expected_bundle_sha256=file_sha256(teacher / "manifest.json")
    )
    digest = file_sha256(manifest)
    with pytest.raises(FileExistsError):
        releases.write_release_new(
            teacher, manifest.parent, expected_bundle_sha256=file_sha256(teacher / "manifest.json")
        )
    with pytest.raises(FileExistsError):
        releases.restore_release_new(
            manifest.parent, manifest.parent, expected_release_sha256=digest
        )
    assert file_sha256(manifest) == digest


def test_relocated_release_is_independent_of_original(teacher: Path, tmp_path: Path) -> None:
    manifest = releases.write_release_new(
        teacher, tmp_path / "release", expected_bundle_sha256=file_sha256(teacher / "manifest.json")
    )
    digest = file_sha256(manifest)
    shutil.move(str(manifest.parent), str(tmp_path / "moved"))
    releases.restore_release_new(
        tmp_path / "moved", tmp_path / "recovered", expected_release_sha256=digest
    )
    assert (
        read_json(tmp_path / "recovered" / "restart.json")["probe"]["predicted_label"] == "circle"
    )


def test_quality_uses_label_support_and_no_labels_stays_unknown(teacher: Path) -> None:
    classifier = load_trusted_local_classifier(teacher, file_sha256(teacher / "manifest.json"))
    report = demo.measure_window(classifier, "partial", ["triangle", "square"], ["triangle", None])
    assert report["count"] == 2
    assert report["labeled_count"] == 1
    assert report["accuracy"] == 0.0
    assert report["triangle_token_fraction"] == 0.5
    assert report["predicted_proportions"] == {"circle": 0.5, "square": 0.5, "triangle": 0.0}
    unknown = demo.measure_window(classifier, "late", ["triangle"], [None])
    assert unknown["accuracy"] is None
    assert unknown["label_availability"] == "absent"
    assert len(report["requests"]) == 2
    assert all(row["seconds"] >= 0 for row in report["requests"])


def test_changed_label_relation_can_degrade_without_input_shift(teacher: Path) -> None:
    classifier = load_trusted_local_classifier(teacher, file_sha256(teacher / "manifest.json"))
    baseline = demo.measure_window(classifier, "base", ["circle", "square"], ["circle", "square"])
    changed = demo.measure_window(classifier, "change", ["circle", "square"], ["square", "circle"])
    assert baseline["triangle_token_fraction"] == changed["triangle_token_fraction"] == 0.0
    assert baseline["predicted_proportions"] == changed["predicted_proportions"]
    assert baseline["accuracy"] == 1.0
    assert changed["accuracy"] == 0.0


@pytest.mark.parametrize("truths", [[], ["unknown"], [True]])
def test_window_rejects_invalid_label_evidence(teacher: Path, truths: list[Any]) -> None:
    classifier = load_trusted_local_classifier(teacher, file_sha256(teacher / "manifest.json"))
    with pytest.raises(ValueError, match="label"):
        demo.measure_window(classifier, "bad", ["circle"], truths)


def test_full_author_demo_measures_windows_and_reuses_recovery(tmp_path: Path) -> None:
    output = demo.run_demo(tmp_path / "demo")
    report = read_json(output / "lifecycle.json")
    assert report["registry"] == "NOT_RUN"
    assert report["index_rollback"] == "NOT_RUN"
    assert [window["accuracy"] for window in report["windows"]] == [1.0, 0.5, 0.0, None]
    assert [window["count"] for window in report["windows"]] == [4, 4, 4, 4]
    assert (
        read_json(output / "recovered-A" / "restart.json")["probe"]["predicted_label"] == "circle"
    )
    root = ET.parse(output / "monitoring.svg").getroot()
    assert root.tag.endswith("svg")
    assert len(list(root.iter("{http://www.w3.org/2000/svg}rect"))) > 4
    with pytest.raises(FileExistsError):
        demo.run_demo(output)
