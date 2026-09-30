"""Acceptance contracts; only explicit learner NotImplementedError becomes xfail."""

from copy import deepcopy
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from roadmap_tools.exercise import exercise_call

torch = pytest.importorskip("torch", reason="Install the optional training group")
fixture = import_module("labs.01_pytorch_foundations.exercises.resume_training.fixture")
starter = import_module("labs.01_pytorch_foundations.exercises.resume_training.starter")


def captured(stop: int = 3) -> tuple[Any, Any, Any, dict[str, Any], list[Any]]:
    model, optimizer, cursor = fixture.new_run()
    cursor, trace = fixture.advance(model, optimizer, cursor, stop)
    state = exercise_call(starter.capture_state, model, optimizer, cursor, fixture.IDENTITY)
    return model, optimizer, cursor, state, trace


@pytest.mark.parametrize("stop", [3, 4])
def test_same_trajectory_in_fresh_process(stop: int, tmp_path: Path) -> None:
    baseline = fixture.fresh_run(tmp_path / "continuous.pt")
    model, optimizer, cursor, state, prefix = captured(stop)
    path = tmp_path / "checkpoint.pt"
    fixture.save_checkpoint(path, state)
    # Probe the precise TODO boundary here; child failures are never blanket xfailed.
    new_model, new_optimizer, _ = fixture.new_run(999)
    restored = exercise_call(
        starter.restore_state,
        new_model,
        new_optimizer,
        fixture.load_checkpoint(path),
        fixture.IDENTITY,
    )
    assert restored == cursor
    assert state.keys() >= {"model", "optimizer", "cursor", "identity", "rng"}
    assert state["rng"].keys() == {"python", "numpy", "torch"}
    fixture.assert_same(state["model"], model.state_dict())
    fixture.assert_same(state["optimizer"], optimizer.state_dict())
    resumed = fixture.fresh_run(tmp_path / "resumed.pt", checkpoint=path)
    assert baseline["pid"] != resumed["pid"]
    fixture.assert_same(baseline["trace"], prefix + resumed["trace"])
    for key in ("model", "optimizer", "cursor", "next_rng", "inference"):
        fixture.assert_same(baseline[key], resumed[key])
    assert baseline["next_rng"] == resumed["next_rng"]
    assert len(baseline["trace"][3]["ids"]) == 1
    assert baseline["trace"][4]["epoch"] == 1


def test_capture_is_independent_of_later_parameter_updates() -> None:
    model, optimizer, cursor, state, _ = captured()
    saved = deepcopy(state)
    fixture.advance(model, optimizer, cursor, 4)
    fixture.assert_same(state, saved)


@pytest.mark.parametrize("missing", ["optimizer", "rng", "cursor"])
def test_restore_requires_complete_training_state(missing: str) -> None:
    model, optimizer, _, state, _ = captured()
    state.pop(missing)
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.restore_state, model, optimizer, state, fixture.IDENTITY)


@pytest.mark.parametrize("missing", ["python", "numpy", "torch"])
def test_restore_requires_each_used_rng(missing: str) -> None:
    model, optimizer, _, state, _ = captured()
    state["rng"].pop(missing)
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.restore_state, model, optimizer, state, fixture.IDENTITY)


@pytest.mark.parametrize("field", ["config", "data", "split"])
def test_restore_rejects_wrong_identity(field: str) -> None:
    model, optimizer, _, state, _ = captured()
    wrong = dict(fixture.IDENTITY, **{field: "wrong"})
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.restore_state, model, optimizer, state, wrong)


@pytest.mark.parametrize("offset", [-1, 12, 8, 6])
def test_restore_rejects_invalid_or_replayed_cursor(offset: int) -> None:
    model, optimizer, _, state, _ = captured()
    state["cursor"]["next_batch_offset"] = offset
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.restore_state, model, optimizer, state, fixture.IDENTITY)


def test_restore_rejects_incompatible_model() -> None:
    _, _, _, state, _ = captured()
    model = torch.nn.Linear(4, 3)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.03, momentum=0.8)
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.restore_state, model, optimizer, state, fixture.IDENTITY)
