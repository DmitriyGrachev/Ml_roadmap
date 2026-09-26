"""Checks for stable, JSON-compatible provenance without loading artifacts."""

import hashlib
import json
from importlib import import_module

import pytest

example = import_module("modules.04_machine_learning.06_reproducibility.example")


def test_manifest_identifies_exact_bytes_and_versions() -> None:
    manifest = example.sensor_manifest()
    assert manifest == example.sensor_manifest()
    assert (
        manifest["data_sha256"]
        == hashlib.sha256(b"sensor,temperature\nA,18.0\nB,21.0\n").hexdigest()
    )
    assert manifest["seed"] == 31
    assert manifest["python"]
    assert manifest["numpy"]
    assert manifest["scikit_learn"]
    assert json.loads(json.dumps(manifest, allow_nan=False)) == manifest


def test_main_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    example.main()
    first = capsys.readouterr().out
    example.main()
    assert capsys.readouterr().out == first
