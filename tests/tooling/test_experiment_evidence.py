"""Portable artifact and identity checks shared by experiment exercises."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity() -> dict[str, object]:
    return {
        "schema_version": 1,
        "exercise_id": "ml-tabular-study",
        "dataset_sha256": "a" * 64,
        "split_sha256": "b" * 64,
        "config": {"seed": 7, "model": {"rate": 0.25, "features": ["age", "balance"]}},
    }


@pytest.mark.parametrize(
    "invalid_path",
    ["../outside.bin", "C:/outside.bin", "C:outside.bin", "/outside.bin", r"..\outside.bin"],
)
def test_artifact_rejects_missing_corrupt_escape(tmp_path: Path, invalid_path: str) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "sample.bin").write_bytes(b"saved bytes")
    with pytest.raises(ValueError, match="missing"):
        checked_artifact(root, "missing.bin", _digest(b"saved bytes"))
    with pytest.raises(ValueError, match="saved bytes"):
        checked_artifact(root, "sample.bin", _digest(b"different bytes"))
    with pytest.raises(ValueError, match="portable relative"):
        checked_artifact(root, invalid_path, _digest(b"saved bytes"))


def test_artifact_rejects_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    link = root / "linked.bin"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("file symlinks are unavailable on this machine")
    with pytest.raises(ValueError, match="escapes"):
        checked_artifact(root, "linked.bin", _digest(b"outside"))


def test_identity_rejects_wrong_exercise_stale_split() -> None:
    manifest = _identity()
    for key, value in (
        ("exercise_id", "another-exercise"),
        ("split_sha256", "c" * 64),
        ("dataset_sha256", "d" * 64),
    ):
        changed = {**manifest, key: value}
        with pytest.raises(ValueError, match=key):
            validate_identity(
                changed,
                exercise_id="ml-tabular-study",
                dataset_sha256="a" * 64,
                split_sha256="b" * 64,
            )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("config", []),
        ("config", {"rate": float("nan")}),
        ("config", {"nested": [0.1, {"value": float("inf")}]}),
        ("config", {"nested": {1: "non-string key"}}),
        ("config", {"nested": ("tuple",)}),
        ("dataset_sha256", "A" * 64),
    ],
)
def test_identity_rejects_malformed_fields(field: str, value: object) -> None:
    manifest = {**_identity(), field: value}
    with pytest.raises(ValueError, match=r"schema_version|config|dataset_sha256"):
        validate_identity(
            manifest,
            exercise_id="ml-tabular-study",
            dataset_sha256="a" * 64,
            split_sha256="b" * 64,
        )


def test_valid_fixture_is_read_only(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    saved = root / "sample.bin"
    original = b"fixture snapshot\x00\xff"
    saved.write_bytes(original)
    manifest = _identity()

    assert checked_artifact(root, "sample.bin", _digest(original)) == saved.resolve()
    validate_identity(
        manifest,
        exercise_id="ml-tabular-study",
        dataset_sha256="a" * 64,
        split_sha256="b" * 64,
    )
    assert saved.read_bytes() == original
    assert manifest == _identity()


def test_identity_accepts_arbitrarily_large_finite_integer() -> None:
    manifest = {**_identity(), "config": {"count": 10**1000}}

    validate_identity(
        manifest,
        exercise_id="ml-tabular-study",
        dataset_sha256="a" * 64,
        split_sha256="b" * 64,
    )
