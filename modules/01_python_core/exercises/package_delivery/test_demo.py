"""Catch source-tree imports masquerading as delivered installed software."""

import json
import os
import subprocess
from pathlib import Path

from .demo import build_and_install

EXAMPLE_PROJECT = Path(__file__).with_name("example_project")


def test_clean_environment_runs_installed_module_from_outside_source(tmp_path: Path) -> None:
    python = build_and_install(EXAMPLE_PROJECT, tmp_path / "delivery")
    outside = tmp_path / "outside"
    outside.mkdir()
    environment = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    result = subprocess.run(
        [str(python), "-I", "-m", "parcel_features"],
        cwd=outside,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["train"] == [[2.5, 8.0], [0.0, 4.0]]
    assert payload["serve"] == [2.5, 8.0]
    probe = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import parcel_features,sys,json; "
            "print(json.dumps([parcel_features.__file__,sys.prefix,sys.base_prefix]))",
        ],
        cwd=outside,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    installed_file, prefix, base_prefix = json.loads(probe.stdout)
    assert Path(installed_file).is_relative_to(Path(prefix))
    assert prefix != base_prefix
    assert not Path(installed_file).is_relative_to(EXAMPLE_PROJECT)


def test_installed_transform_validates_data_and_handles_unicode(tmp_path: Path) -> None:
    python = build_and_install(EXAMPLE_PROJECT, tmp_path / "delivery")
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "from parcel_features.transform import transform; "
            "assert transform({'weight_grams':500,'destination':'  Iași   Nord '}) == [0.5,9.0]; "
            "transform({'weight_grams':-1,'destination':'x'})",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ValueError: weight_grams" in result.stderr
