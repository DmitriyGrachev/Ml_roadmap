"""Generator regressions: explicit, finite, reproducible and non-destructive."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from .generate import generate

MODULE = "modules.03_data_foundations.exercises.data_release.generate"


@pytest.mark.parametrize("records", [0, -1, True])
def test_invalid_size_creates_nothing(tmp_path: Path, records: int) -> None:
    target = tmp_path / "new"
    with pytest.raises(ValueError, match="records"):
        generate(target, records=records, seed=7)
    assert not target.exists()


def test_existing_directory_is_preserved(tmp_path: Path) -> None:
    marker = tmp_path / "notes.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        generate(tmp_path, records=10, seed=7)
    assert marker.read_text(encoding="utf-8") == "keep"
    assert list(tmp_path.iterdir()) == [marker]


def test_repeat_has_identical_bytes_and_real_provenance(tmp_path: Path) -> None:
    first, second = tmp_path / "a", tmp_path / "b"
    generate(first, records=31, seed=19)
    generate(second, records=31, seed=19)
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    provenance = json.loads((first / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["records"] == 31
    assert provenance["origin"] == "local synthetic teaching fixture"
    assert provenance["license"] == "CC0-1.0"
    for name, digest in provenance["sources"].items():
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == digest
    assert (
        sum(
            len((first / name).read_text().splitlines()) - offset
            for name, offset in [("source_a.csv", 1), ("source_b.jsonl", 0)]
        )
        == 31
    )


def test_cli_requires_output_and_defaults_to_small_profile(tmp_path: Path) -> None:
    missing = subprocess.run([sys.executable, "-m", MODULE], capture_output=True, text=True)
    assert missing.returncode == 2
    target = tmp_path / "explicit"
    result = subprocess.run([sys.executable, "-m", MODULE, str(target)], capture_output=True)
    assert result.returncode == 0, result.stderr
    provenance = json.loads((target / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["records"] == 200
