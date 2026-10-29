"""Pure audit contracts, independent of MLflow/Optuna and learner solutions."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any


def digest(value: Any) -> str:
    """Hash canonical UTF-8 JSON; list order is part of the dataset identity."""
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def objective_inputs(dataset: dict[str, Any]) -> dict[str, Any]:
    """Validate split/family/text disjointness; expose no holdout to the objective."""
    if set(dataset) != {"train", "dev", "holdout"}:
        raise ValueError("exactly train/dev/holdout splits required")
    seen: dict[str, set[str]] = {key: set() for key in ("id", "family", "text")}
    labels: dict[str, set[str]] = {}
    for split in ("train", "dev", "holdout"):
        rows = dataset[split]
        if not isinstance(rows, list) or not 2 <= len(rows) <= 2000:
            raise ValueError("each split needs 2..2000 rows")
        current: dict[str, set[str]] = {key: set() for key in seen}
        labels[split] = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"id", "family", "text", "label"}:
                raise ValueError("row requires id/family/text/label")
            if any(not isinstance(v, str) or not v.strip() or len(v) > 10000 for v in row.values()):
                raise ValueError("row values must be bounded nonempty strings")
            labels[split].add(row["label"])
            for key in seen:
                value = " ".join(row[key].casefold().split()) if key == "text" else row[key]
                if value in seen[key] or (key == "id" and value in current[key]):
                    raise ValueError(f"split {key} overlap")
                current[key].add(value)
        for key in seen:
            seen[key].update(current[key])
    if len(labels["train"]) < 2 or any(labels[s] != labels["train"] for s in ("dev", "holdout")):
        raise ValueError("all splits must represent the same two or more labels")
    return copy.deepcopy({s: dataset[s] for s in ("train", "dev")})


def split_digest(dataset: dict[str, Any]) -> str:
    return digest({split: [r["id"] for r in dataset[split]] for split in sorted(dataset)})


def select_best(trials: list[dict[str, Any]], direction: str) -> int:
    """Audit oracle: complete finite trials only; smallest trial number breaks ties."""
    if direction not in {"maximize", "minimize"}:
        raise ValueError("direction must be maximize or minimize")
    complete = []
    numbers: set[int] = set()
    for row in trials:
        number = row.get("number")
        if type(number) is not int or number < 0 or number in numbers:
            raise ValueError("unique nonnegative trial numbers required")
        numbers.add(number)
        if row.get("state") not in {"COMPLETE", "FAIL", "PRUNED"}:
            raise ValueError("unknown trial state")
        if row["state"] == "COMPLETE":
            value = row.get("value")
            if (
                isinstance(value, bool)
                or not isinstance(value, (float, int))
                or not math.isfinite(value)
            ):
                raise ValueError("complete objective must be finite")
            complete.append(row)
    if not complete:
        raise ValueError("no complete trials")
    sign = -1 if direction == "maximize" else 1
    winner = min(complete, key=lambda row: (sign * row["value"], row["number"]))
    return int(winner["number"])


def macro_f1(labels: list[str], predictions: list[str]) -> float:
    """Mean class F1 on a fixed label universe; reject missing/misaligned outputs."""
    if not labels or len(labels) != len(predictions) or set(predictions) - set(labels):
        raise ValueError("predictions must align with labels and their known universe")
    values = []
    for label in sorted(set(labels)):
        tp = sum(a == label and b == label for a, b in zip(labels, predictions, strict=True))
        fp = sum(a != label and b == label for a, b in zip(labels, predictions, strict=True))
        fn = sum(a == label and b != label for a, b in zip(labels, predictions, strict=True))
        values.append(2 * tp / (2 * tp + fp + fn))
    return sum(values) / len(values)


def validate_table(
    trials: list[dict[str, Any]], labels: list[str], *, selected: int, budget: int
) -> int:
    """Recompute every complete trial metric and audit maximization before holdout."""
    if type(budget) is not int or not 1 <= budget <= 4 or len(trials) != budget:
        raise ValueError("budget must be 1..4 and account for all trials")
    winner = select_best(trials, "maximize")
    if {row["number"] for row in trials} != set(range(budget)):
        raise ValueError("trial table must cover the declared budget")
    for row in trials:
        if row["state"] == "COMPLETE" and not math.isclose(
            row["value"], macro_f1(labels, row["dev_predictions"]), abs_tol=1e-12
        ):
            raise ValueError("trial metric differs from dev predictions")
    if type(selected) is not int or selected != winner:
        raise ValueError("selected trial differs from validation winner")
    return winner
