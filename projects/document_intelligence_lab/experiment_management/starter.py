"""Learner boundaries. Do not import/call demo or protocol.select_best as a solution."""

from collections.abc import Callable
from pathlib import Path
from typing import Any


def select_trial(trials: list[dict[str, Any]], direction: str) -> int:
    """Finite COMPLETE trials, explicit direction, smallest-number tie break."""
    raise NotImplementedError("Implement independent direction/state-aware trial selection")


def build_objective(
    train: list[dict[str, str]], dev: list[dict[str, str]], *, seed: int
) -> Callable[[Any], float]:
    """Return Optuna objective: fit train only; set dev_predictions and return macro F1."""
    raise NotImplementedError("Implement sklearn pipeline search objective without holdout")


def run_search(dataset: dict[str, Any], output: Path, *, seed: int = 23, budget: int = 4) -> Path:
    """Bounded actual Optuna/MLflow run; independently log, select, save and reload model."""
    raise NotImplementedError("Implement independent local search/log/reload; see README contract")
