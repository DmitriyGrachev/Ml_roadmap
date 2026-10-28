"""Author checks: only the owned draft may disappear on either failure phase."""

import os
import runpy
from pathlib import Path
from typing import Any, NoReturn

import pytest


@pytest.fixture
def lesson() -> dict[str, Any]:
    return runpy.run_path(str(Path(__file__).parents[1] / "06_exceptions_io/walkthrough.py"))


def test_notice_replaces_bytes_and_consumes_only_its_draft(
    lesson: dict[str, Any], tmp_path: Path
) -> None:
    target = tmp_path / "notice.txt"
    target.write_bytes(b"old")
    unrelated = tmp_path / "keep.tmp"
    unrelated.write_bytes(b"other owner")
    lesson["publish_notice"](target)
    assert target.read_bytes() == b"Library closes at 18:00.\n"
    assert unrelated.read_bytes() == b"other owner"
    assert set(tmp_path.iterdir()) == {target, unrelated}


def test_real_serialization_failure_preserves_old_bytes(
    lesson: dict[str, Any], tmp_path: Path
) -> None:
    target = tmp_path / "catalog.json"
    target.write_bytes(b"old catalog")
    unrelated = tmp_path / "keep.tmp"
    unrelated.write_bytes(b"other owner")
    with pytest.raises(TypeError, match="set is not JSON serializable"):
        lesson["serialize_broken_catalog"](tmp_path)
    assert target.read_bytes() == b"old catalog"
    assert unrelated.read_bytes() == b"other owner"
    assert set(tmp_path.iterdir()) == {target, unrelated}


@pytest.mark.parametrize("phase", ["serialize", "replace"])
def test_failure_keeps_original_exception_object(
    lesson: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    target = tmp_path / "notice.txt"
    target.write_bytes(b"old")
    unrelated = tmp_path / "keep.tmp"
    unrelated.write_bytes(b"other owner")
    original = TypeError("cannot encode") if phase == "serialize" else OSError("cannot replace")

    def fail(*_args: object, **_kwargs: object) -> NoReturn:
        raise original

    if phase == "serialize":
        monkeypatch.setattr(lesson["serialize_broken_catalog"].__globals__["json"], "dump", fail)
        operation = lesson["serialize_broken_catalog"]
        argument = tmp_path
    else:
        monkeypatch.setattr(os, "replace", fail)
        operation = lesson["publish_notice"]
        argument = target

    with pytest.raises(type(original)) as caught:
        operation(argument)
    assert caught.value is original
    assert target.read_bytes() == b"old"
    assert unrelated.read_bytes() == b"other owner"
    assert set(tmp_path.iterdir()) == {target, unrelated}


def test_cleanup_failure_adds_evidence_without_masking_replacement_error(
    lesson: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "notice.txt"
    target.write_bytes(b"old")
    original = OSError("replacement denied")

    def fail_replace(*_args: object) -> NoReturn:
        raise original

    def fail_unlink(*_args: object, **_kwargs: object) -> NoReturn:
        raise PermissionError("cleanup denied")

    monkeypatch.setattr(os, "replace", fail_replace)
    monkeypatch.setattr(Path, "unlink", fail_unlink)
    with pytest.raises(OSError, match="replacement denied") as caught:
        lesson["publish_notice"](target)
    assert caught.value is original
    assert any("cleanup denied" in note for note in original.__notes__)
    assert target.read_bytes() == b"old"
    assert len(list(tmp_path.glob("notice-*.tmp"))) == 1
