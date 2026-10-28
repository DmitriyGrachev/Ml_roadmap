"""Coupled author boundary tests using tiny bytes, never a pretrained model run."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Any, cast

import httpx
import pytest

from projects.document_intelligence_lab.artifacts import file_sha256, json_bytes, read_json
from projects.document_intelligence_lab.part_a1.demo import run_demo

dense = importlib.import_module("labs.03_real_rag.dense")
releases = importlib.import_module("labs.06_ml_lifecycle.releases")
ORIGINAL_CONNECT = socket.socket.connect


def api() -> Any:
    assert importlib.util.find_spec("labs.06_ml_lifecycle.coupled") is not None, (
        "coupled release implementation is missing"
    )
    return importlib.import_module("labs.06_ml_lifecycle.coupled")


@pytest.fixture(autouse=True)
def only_eventloop_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def connect(connection: socket.socket, address: Any) -> None:
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return ORIGINAL_CONNECT(connection, address)
        raise RuntimeError("external network forbidden")

    def deny(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("TCP HTTP forbidden")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", deny)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", deny)


@pytest.fixture(scope="module")
def teacher(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return run_demo(tmp_path_factory.mktemp("coupled-teacher") / "teacher")


def tiny_model(directory: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    directory.mkdir()
    files = []
    for name in (
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
        "model.safetensors",
    ):
        content = ("FIXTURE_NOT_PRETRAINED:" + name).encode()
        (directory / name).write_bytes(content)
        files.append(
            {
                "filename": name,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    model = {"id": "UNIT_FIXTURE_NOT_PRETRAINED", "revision": "unit-only", "files": files}
    monkeypatch.setattr(
        importlib.import_module("labs.02_huggingface_models.download"),
        "resource_manifest",
        lambda: {"model": model},
    )
    return model


@pytest.fixture
def inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, teacher: Path) -> dict[str, Any]:
    model = tmp_path / "input-model"
    resource = tiny_model(model, monkeypatch)
    snapshot = tmp_path / "input-snapshot"
    demo = importlib.import_module("labs.03_real_rag.demo")
    # Private is closest to public first chunk, but cannot occupy its top-k slot.
    vectors = [
        [1.0, 0.0] + [0.0] * 382,
        [0.0, 1.0] + [0.0] * 382,
        [1.0, 0.0] + [0.0] * 382,
        [-1.0, 0.0] + [0.0] * 382,
    ]
    snapshot_pin = dense.write_snapshot(
        snapshot, demo.teacher_sources(), vectors, dense.verified_minilm_identity(model)
    )
    classification = tmp_path / "input-classification"
    release = releases.write_release_new(
        teacher / "rules",
        classification,
        expected_bundle_sha256=file_sha256(teacher / "rules/manifest.json"),
    )
    return {
        "model": model,
        "resource": resource,
        "snapshot": snapshot,
        "classification": classification,
        "classification_pin": file_sha256(release),
        "snapshot_pin": snapshot_pin,
        "teacher": teacher,
    }


def build(inputs: dict[str, Any], output: Path) -> Path:
    return cast(
        Path,
        api().write_coupled_release_new(
            inputs["classification"],
            inputs["snapshot"],
            inputs["model"],
            output,
            expected_classification_release_sha256=inputs["classification_pin"],
            expected_snapshot_sha256=inputs["snapshot_pin"],
        ),
    )


def test_release_copies_complete_independent_suite_and_real_asgi_restart(
    inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    manifest = build(inputs, tmp_path / "release")
    pin = file_sha256(manifest)
    for key in ("classification", "snapshot", "model"):
        shutil.rmtree(inputs[key])
    verified = api().verify_coupled_release(manifest.parent, expected_release_sha256=pin)
    assert verified["generator"] is None
    assert verified["embedding"]["pooling"] == "first-token-last-hidden-state-l2-v1"
    assert len(list((manifest.parent / "model").iterdir())) == 6
    recovered = api().restore_coupled_release_new(
        manifest.parent,
        tmp_path / "recovered",
        expected_release_sha256=pin,
    )
    restart = read_json(recovered / "classification/restart.json")
    assert restart["ready"] is True
    assert restart["probe"]["predicted_label"] == "circle"
    receipt = read_json(recovered / "recovery.json")
    assert receipt["process_id"] == os.getpid()
    assert receipt["release_sha256"] == pin
    assert receipt["generation"] == "NOT_RUN"


@pytest.mark.parametrize("key", ["classification_pin", "snapshot_pin"])
def test_wrong_nested_pin_leaves_no_output(
    inputs: dict[str, Any], tmp_path: Path, key: str
) -> None:
    inputs[key] = "0" * 64
    with pytest.raises(ValueError, match=r"sha256|manifest"):
        build(inputs, tmp_path / "release")
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize(
    "target", ["model/config.json", "snapshot/sources.json", "classification/bundle/model.json"]
)
def test_nested_byte_tamper_rejected(inputs: dict[str, Any], tmp_path: Path, target: str) -> None:
    manifest = build(inputs, tmp_path / "release")
    pin = file_sha256(manifest)
    path = manifest.parent / target
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match=r"sha256|artifact"):
        api().verify_coupled_release(manifest.parent, expected_release_sha256=pin)


@pytest.mark.parametrize("field", ["embedding", "index", "corpus", "classification", "code"])
def test_outer_identity_tamper_rejected_even_if_repinned(
    inputs: dict[str, Any],
    tmp_path: Path,
    field: str,
) -> None:
    manifest = build(inputs, tmp_path / "release")
    value = read_json(manifest)
    value[field] = {"tampered": True}
    manifest.write_bytes(json_bytes(value))
    with pytest.raises(ValueError, match="identity"):
        api().verify_coupled_release(manifest.parent, expected_release_sha256=file_sha256(manifest))


@pytest.mark.parametrize(
    ("field", "value"),
    [("max_length", 64), ("pooling", "mean"), ("device", "cuda"), ("batch_size", 1)],
)
def test_same_dimension_different_representation_cannot_publish(
    inputs: dict[str, Any],
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    manifest = inputs["snapshot"] / "manifest.json"
    data = read_json(manifest)
    data["embedding"][field] = value
    manifest.write_bytes(json_bytes(data))
    inputs["snapshot_pin"] = file_sha256(manifest)
    with pytest.raises(ValueError, match="representation"):
        build(inputs, tmp_path / "release")
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize("root", ["model", "snapshot", "classification"])
def test_unlisted_files_cannot_publish(inputs: dict[str, Any], tmp_path: Path, root: str) -> None:
    (inputs[root] / "extra.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="inventory"):
        build(inputs, tmp_path / "release")
    assert not (tmp_path / "release").exists()


def test_contained_symlink_cannot_publish(inputs: dict[str, Any], tmp_path: Path) -> None:
    path = inputs["snapshot"] / "sources.json"
    original = inputs["snapshot"] / "hidden-sources.json"
    path.rename(original)
    try:
        path.symlink_to(original)
    except OSError as exc:
        pytest.skip(f"Windows symlink privilege unavailable: {exc}")
    with pytest.raises(ValueError, match="link"):
        build(inputs, tmp_path / "release")
    assert not (tmp_path / "release").exists()


def test_no_overwrite_or_source_digest_autotrust(inputs: dict[str, Any], tmp_path: Path) -> None:
    manifest = build(inputs, tmp_path / "release")
    pin = file_sha256(manifest)
    with pytest.raises(FileExistsError):
        build(inputs, manifest.parent)
    with pytest.raises(FileExistsError):
        api().restore_coupled_release_new(
            manifest.parent, manifest.parent, expected_release_sha256=pin
        )
    with pytest.raises(ValueError, match="sha256"):
        api().verify_coupled_release(manifest.parent, expected_release_sha256="0" * 64)


def test_pickle_restore_requires_separate_explicit_trust(
    inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    release = releases.write_release_new(
        inputs["teacher"] / "tfidf-linear",
        tmp_path / "pickle-release",
        expected_bundle_sha256=file_sha256(inputs["teacher"] / "tfidf-linear/manifest.json"),
    )
    inputs["classification"] = release.parent
    inputs["classification_pin"] = file_sha256(release)
    manifest = build(inputs, tmp_path / "release")
    with pytest.raises(ValueError, match="trust"):
        api().restore_coupled_release_new(
            manifest.parent, tmp_path / "denied", expected_release_sha256=file_sha256(manifest)
        )
    assert not (tmp_path / "denied").exists()


def test_base_verify_imports_no_torch_transformers_or_qdrant(
    inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    manifest = build(inputs, tmp_path / "release")
    script = """
import importlib, json, sys
from pathlib import Path
class Block:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'transformers', 'qdrant_client'}:
            raise RuntimeError('forbidden heavy import: ' + fullname)
sys.meta_path.insert(0, Block())
resource = json.loads(sys.argv[3])
downloader = importlib.import_module('labs.02_huggingface_models.download')
downloader.resource_manifest = lambda: {'model': resource}
module = importlib.import_module('labs.06_ml_lifecycle.coupled')
module.verify_coupled_release(Path(sys.argv[1]), expected_release_sha256=sys.argv[2])
"""
    subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(manifest.parent),
            file_sha256(manifest),
            json_bytes(inputs["resource"]).decode(),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_cli_requires_external_pin_and_never_overwrites_receipt(tmp_path: Path) -> None:
    api()
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "labs.06_ml_lifecycle.coupled",
            "verify",
            "--root",
            str(tmp_path),
            "--receipt",
            str(tmp_path / "receipt.json"),
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "--release-sha256" in completed.stderr
    assert not (tmp_path / "receipt.json").exists()


def test_encode_local_observations_are_accepted_as_input_but_not_copied(
    inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    for name in ("retrieval-comparison.json", "query-evidence.json"):
        (inputs["snapshot"] / name).write_bytes(b'{"observation_only": true}')
    manifest = build(inputs, tmp_path / "release")
    assert {path.name for path in (manifest.parent / "snapshot").iterdir()} == {
        "manifest.json",
        "sources.json",
        "chunks.json",
        "vectors.json",
    }
    # The verified release has a strict inventory, even for source-only observations.
    (manifest.parent / "snapshot/query-evidence.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="inventory"):
        api().verify_coupled_release(manifest.parent, expected_release_sha256=file_sha256(manifest))


@pytest.mark.parametrize("command", ["write", "verify", "restore", "index", "verify-index"])
def test_cli_rejects_receipt_inside_input_or_output_before_mutation(
    inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
) -> None:
    manifest = build(inputs, tmp_path / "release")
    receipt = manifest.parent / "unlisted-receipt.json"
    if command == "write":
        args = [
            "write",
            "--classification-release",
            str(inputs["classification"]),
            "--classification-release-sha256",
            inputs["classification_pin"],
            "--snapshot",
            str(inputs["snapshot"]),
            "--snapshot-sha256",
            inputs["snapshot_pin"],
            "--model-dir",
            str(inputs["model"]),
            "--output",
            str(tmp_path / "output"),
        ]
        receipt = tmp_path / "output/receipt.json"
    else:
        args = [command, "--root", str(manifest.parent), "--release-sha256", file_sha256(manifest)]
        if command == "restore":
            args += ["--output", str(tmp_path / "output")]
        elif command in {"index", "verify-index"}:
            args += ["--storage", str(tmp_path / "storage")]
    monkeypatch.setattr(sys, "argv", ["coupled", *args, "--receipt", str(receipt)])
    with pytest.raises(ValueError, match=r"receipt.*outside"):
        api().main()
    assert not receipt.exists()
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "storage").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction boundary")
@pytest.mark.parametrize("target", ["input", "output"])
def test_junction_in_ancestor_path_is_rejected(
    inputs: dict[str, Any],
    tmp_path: Path,
    target: str,
) -> None:
    alias = tmp_path / "alias"
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(alias), str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    output = tmp_path / "release"
    if target == "input":
        inputs["snapshot"] = alias / "input-snapshot"
    else:
        output = alias / "release"
    with pytest.raises(ValueError, match="link"):
        build(inputs, output)
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize("operation", ["write", "restore", "index"])
def test_new_output_cannot_mutate_a_pinned_input_tree(
    inputs: dict[str, Any],
    tmp_path: Path,
    operation: str,
) -> None:
    manifest = build(inputs, tmp_path / "release")
    output = manifest.parent / "nested-output"
    if operation == "write":
        output = inputs["snapshot"] / "nested-output"
        action = partial(build, inputs, output)
    elif operation == "restore":
        action = partial(
            api().restore_coupled_release_new,
            manifest.parent,
            output,
            expected_release_sha256=file_sha256(manifest),
        )
    else:
        action = partial(
            api().restore_index_new,
            manifest.parent,
            output,
            expected_release_sha256=file_sha256(manifest),
        )
    with pytest.raises(ValueError, match=r"output.*outside"):
        action()
    assert not output.exists()


def test_existing_cli_receipt_is_not_overwritten_and_has_no_output_side_effect(
    inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = build(inputs, tmp_path / "release")
    receipt = tmp_path / "receipt.json"
    receipt.write_bytes(b"KEEP OPERATOR RECEIPT")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coupled",
            "restore",
            "--root",
            str(manifest.parent),
            "--release-sha256",
            file_sha256(manifest),
            "--output",
            str(tmp_path / "recovered"),
            "--receipt",
            str(receipt),
        ],
    )
    with pytest.raises(FileExistsError):
        api().main()
    assert receipt.read_bytes() == b"KEEP OPERATOR RECEIPT"
    assert not (tmp_path / "recovered").exists()


def test_snapshot_preprocessing_change_fails_even_with_updated_pin(
    inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    manifest = inputs["snapshot"] / "manifest.json"
    data = read_json(manifest)
    data["chunking"] = "incompatible chunking"
    manifest.write_bytes(json_bytes(data))
    inputs["snapshot_pin"] = file_sha256(manifest)
    with pytest.raises(ValueError, match="preprocessing"):
        build(inputs, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_explicit_trusted_pickle_recovery_uses_actual_classifier(
    inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    release = releases.write_release_new(
        inputs["teacher"] / "tfidf-linear",
        tmp_path / "pickle",
        expected_bundle_sha256=file_sha256(inputs["teacher"] / "tfidf-linear/manifest.json"),
    )
    inputs["classification"] = release.parent
    inputs["classification_pin"] = file_sha256(release)
    manifest = build(inputs, tmp_path / "release")
    recovered = api().restore_coupled_release_new(
        manifest.parent,
        tmp_path / "recovered",
        expected_release_sha256=file_sha256(manifest),
        trusted_local_artifact=True,
    )
    assert read_json(recovered / "classification/restart.json")["ready"] is True
    assert (
        read_json(recovered / "classification/restart.json")["probe"]["predicted_label"]
        == "triangle"
    )
