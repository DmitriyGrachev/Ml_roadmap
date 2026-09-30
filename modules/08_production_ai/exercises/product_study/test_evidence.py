"""Unrelated miniature routing records exercise validator boundaries."""

import importlib
from pathlib import Path
from typing import Any

import pytest


def test_missing_evidence_is_rejected(tmp_path: Path) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    with pytest.raises(ValueError, match="invalid JSON"):
        module.validate_evidence(tmp_path)


def test_measured_totals_and_permissions() -> None:
    module = importlib.import_module(__package__ + ".evidence")
    requests = [
        {"id": "toy-a", "role": "reader", "acceptable": ["desk"]},
        {"id": "toy-b", "role": "reader", "acceptable": []},
    ]
    outputs: list[dict[str, Any]] = [
        {"id": "toy-a", "route": "desk", "latency_ms": 2, "cost_units": 1},
        {"id": "toy-b", "route": None, "latency_ms": 4, "cost_units": 0},
    ]
    catalog = [{"id": "desk", "roles": ["reader"]}]
    assert module.summarize(requests, outputs, catalog) == {
        "count": 2,
        "matched": 1,
        "fallback": 1,
        "latency_ms_total": 6,
        "cost_units_total": 1,
    }
    outputs[0]["route"] = "unknown"
    with pytest.raises(ValueError, match="unknown route"):
        module.summarize(requests, outputs, catalog)


@pytest.mark.parametrize("mutation", ["ids", "permission", "nonfinite", "negative"])
def test_invalid_routes_or_measurements(mutation: str) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    requests = [{"id": "toy", "role": "visitor", "acceptable": []}]
    outputs: list[dict[str, Any]] = [{"id": "toy", "route": None, "latency_ms": 1, "cost_units": 0}]
    if mutation == "ids":
        outputs[0]["id"] = "foreign"
    elif mutation == "permission":
        outputs[0]["route"] = "private"
    elif mutation == "nonfinite":
        outputs[0]["latency_ms"] = float("nan")
    else:
        outputs[0]["cost_units"] = -1
    with pytest.raises(
        ValueError, match=r"IDs differ|permission denied|invalid elapsed|invalid cost"
    ):
        module.summarize(requests, outputs, [{"id": "private", "roles": ["staff"]}])


@pytest.mark.parametrize(
    "change",
    [None, "run", "dataset", "split", "count", "bool", "cost", "latency", "duplicate", "missing"],
)
def test_saved_output_accounting_and_bounds(change: str | None) -> None:
    module = importlib.import_module(__package__ + ".evidence")
    identity = {"run_id": "toy", "dataset_sha256": "a" * 64, "split_sha256": "b" * 64}
    requests = [{"id": "pencil", "role": "guest", "acceptable": []}]
    output: dict[str, Any] = {
        **identity,
        "records": [{"id": "pencil", "route": None, "latency_ms": 2, "cost_units": 1}],
        "accounting": {
            "count": 1,
            "matched": 0,
            "fallback": 1,
            "latency_ms_total": 2.0,
            "cost_units_total": 1,
        },
    }
    constraints = {
        "catalog": [{"id": "desk", "roles": ["staff"]}],
        "max_cost_units_total": 1,
        "max_latency_ms_per_request": 2,
    }
    if change in ("run", "dataset", "split"):
        output[{"run": "run_id", "dataset": "dataset_sha256", "split": "split_sha256"}[change]] = (
            "old"
        )
    elif change == "count":
        output["accounting"]["count"] = 2
    elif change == "bool":
        output["records"][0]["cost_units"] = True
    elif change == "cost":
        constraints["max_cost_units_total"] = 0
    elif change == "latency":
        constraints["max_latency_ms_per_request"] = 1
    elif change == "duplicate":
        output["records"] *= 2
    elif change == "missing":
        output["records"][0].pop("route")
    if change is None:
        module.validate_outputs(requests, constraints, output, identity)
    else:
        with pytest.raises(
            ValueError, match=r"differs|IDs differ|invalid cost|budget|missing route"
        ):
            module.validate_outputs(requests, constraints, output, identity)
