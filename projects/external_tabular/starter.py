"""Собственная работа: готового отчёта или выполненного исследования здесь нет."""

from pathlib import Path


def run_experiment(raw_csv: Path, output: Path, *, seed: int = 23) -> None:
    """Create independent evidence per README, using only train/dev before final evaluation."""
    raise NotImplementedError("Реализуйте внешний tabular experiment и создайте submission")
