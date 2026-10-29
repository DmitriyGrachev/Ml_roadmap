"""Learner credit requires an installed independent package, not the author's demo."""

import json
import subprocess
from pathlib import Path

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import deliver

pytestmark = pytest.mark.student_exercise
PROJECT = Path(__file__).with_name("student_project")


@pytest.fixture(scope="module")
def delivered(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    outside = tmp_path_factory.mktemp("ticket-delivery")
    python = exercise_call(deliver, PROJECT, outside / "delivery")
    assert python.is_file(), "deliver must return the installed environment's Python"
    return python, outside


def test_installed_module_entry_and_shared_features(delivered: tuple[Path, Path]) -> None:
    python, outside = delivered
    result = subprocess.run(
        [str(python), "-I", "-m", "ticket_features"],
        cwd=outside,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == {"train": [[0.25, 2.0], [1.0, 0.0]], "serve": [0.25, 2.0]}
    probe = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import sys,json,ticket_features; "
            "print(json.dumps([sys.prefix,sys.base_prefix,ticket_features.__file__]))",
        ],
        cwd=outside,
        check=True,
        capture_output=True,
        text=True,
    )
    prefix, base, installed_file = json.loads(probe.stdout)
    assert prefix != base
    assert Path(prefix).is_relative_to(outside)
    assert Path(installed_file).is_relative_to(Path(prefix))


def test_unseen_record_consistency_and_input_preservation(delivered: tuple[Path, Path]) -> None:
    python, outside = delivered
    script = (
        "import copy,json; from ticket_features.train import training_matrix; "
        "from ticket_features.serve import serving_vector; "
        "records=[{'duration_minutes':0,'priority':' NORMAL '},"
        "{'duration_minutes':90,'priority':'urgent'}]; original=copy.deepcopy(records); "
        "assert training_matrix(records)==[[0.0,1.0],[0.75,2.0]]; "
        "assert serving_vector(records[1])==[0.75,2.0]; "
        "assert records==original; assert training_matrix([])==[]; print('ok')"
    )
    result = subprocess.run(
        [str(python), "-I", "-c", script], cwd=outside, check=True, capture_output=True, text=True
    )
    assert result.stdout.strip() == "ok"


@pytest.mark.parametrize(
    "record",
    [
        {"duration_minutes": -1, "priority": "low"},
        {"duration_minutes": float("nan"), "priority": "low"},
        {"duration_minutes": float("inf"), "priority": "low"},
        {"duration_minutes": True, "priority": "low"},
        {"duration_minutes": 1, "priority": "unknown"},
    ],
)
def test_invalid_records_rejected_by_installed_transform(
    delivered: tuple[Path, Path],
    record: dict[str, object],
) -> None:
    python, outside = delivered
    script = """import json,sys
from ticket_features.serve import serving_vector
try:
    serving_vector(json.loads(sys.argv[1]))
except ValueError:
    print('rejected')
else:
    raise AssertionError('invalid data accepted')
"""
    result = subprocess.run(
        [str(python), "-I", "-c", script, json.dumps(record)],
        cwd=outside,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "rejected"
