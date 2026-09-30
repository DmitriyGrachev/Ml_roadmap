"""Observed behavior of supplied inputs, without a diagnosis key."""

from importlib import import_module
from pathlib import Path

import pytest

torch = pytest.importorskip("torch", reason="Install the optional training group")
fixtures = import_module("labs.01_pytorch_foundations.debugging.fixtures")


@pytest.mark.parametrize("case_id", ["a", "b", "c", "d"])
def test_records_actual_observations(case_id: str, tmp_path: Path) -> None:
    root = fixtures.run_case(case_id, tmp_path / "observed", seed=23)
    run = fixtures.load_run(root)
    assert run["case_id"] == case_id
    assert run["seed"] == 23
    assert len(run["trace"]) >= 1
    first = run["trace"][0]
    assert first["ids"] == ["sample-0", "sample-1", "sample-2", "sample-3"]
    assert first["before"].numel() > 0
    assert first["train_outputs"][0].shape == (4, 2, 1)
    assert first["step_calls"] == [{"training": True, "grad_enabled": True}]
    assert first["step_dropout_calls"] == [{"training": True, "p": 0.3}]
    assert len(first["validation"]["outputs"]) == 2
    with pytest.raises(AssertionError):
        fixtures.assert_healthy(run)


@pytest.mark.parametrize("case_id", ["a", "b", "c", "d"])
def test_replay_has_same_observations(case_id: str, tmp_path: Path) -> None:
    first = fixtures.load_run(fixtures.run_case(case_id, tmp_path / "one", seed=23))
    second = fixtures.load_run(fixtures.run_case(case_id, tmp_path / "two", seed=23))
    fixtures.assert_same(first, second)


def test_refuses_to_overwrite_existing_output(tmp_path: Path) -> None:
    root = fixtures.run_case("a", tmp_path / "run", seed=23)
    original = (root / "trace.pt").read_bytes()
    with pytest.raises(FileExistsError):
        fixtures.run_case("a", root, seed=23)
    assert (root / "trace.pt").read_bytes() == original


def test_unknown_input_does_not_create_output(tmp_path: Path) -> None:
    target = tmp_path / "run"
    with pytest.raises(ValueError, match="case"):
        fixtures.run_case("unknown", target, seed=23)
    assert not target.exists()


def test_collection_contains_distinct_measurable_outcomes(tmp_path: Path) -> None:
    runs = [
        fixtures.load_run(fixtures.run_case(c, tmp_path / c, seed=23)) for c in fixtures.CASE_IDS
    ]
    assert sum(any(r["error"] is not None for r in run["trace"]) for run in runs) == 1
    assert (
        sum(
            all(torch.equal(r["before"], r["after"]) for r in run["trace"])
            and all(r["error"] is None for r in run["trace"])
            for run in runs
        )
        == 1
    )
    assert (
        sum(
            any(c["grad_enabled"] for r in run["trace"] for c in r["validation"]["calls"])
            for run in runs
        )
        == 1
    )
    assert sum(any(not torch.isfinite(r["after"]).all() for r in run["trace"]) for run in runs) == 1


@pytest.mark.parametrize("fault", ["child_eval", "retained_eval"])
def test_rejects_deterministic_child_during_actual_training(tmp_path: Path, fault: str) -> None:
    # Deliberately incorrect training input: parent training flag hides child eval.
    source = tmp_path / "deterministic_input.py"
    training_setup = "    model.train()\n    model[0].eval()\n" if fault == "child_eval" else ""
    source.write_text(
        "import torch\nCONFIG = {'lr': 0.01, 'steps': 8}\n"
        "def step(model, optimizer, x, y, mask):\n"
        + training_setup
        + "    optimizer.zero_grad(set_to_none=True)\n"
        "    prediction = model(x)\n"
        "    loss = (prediction[mask] - y[mask]).square().mean()\n"
        "    loss.backward()\n"
        "    optimizer.step()\n"
        "    return prediction, loss\n"
        "def validate(model, x):\n"
        "    model.eval()\n"
        "    with torch.no_grad():\n"
        "        return model(x)\n",
        encoding="utf-8",
    )
    run = fixtures.observe(source, seed=23)
    assert all(row["error"] is None for row in run["trace"])
    if fault == "child_eval":
        assert all(
            row["step_calls"] == [{"training": True, "grad_enabled": True}] for row in run["trace"]
        )
    with pytest.raises(AssertionError, match=r"training (stochasticity|context)"):
        fixtures.assert_healthy(run)
    assert all(
        row["step_dropout_calls"] == [{"training": False, "p": 0.3}] for row in run["trace"][1:]
    )
