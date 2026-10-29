"""Внешнее исследование опирается на ваши реализации lab 02, не заменяет их."""

from pathlib import Path


def run_study(cache: Path, output: Path, *, seed: int = 23) -> None:
    """Reuse lab prepare_splits/compare_models with audited groups and locked external split.

    Preserve training history, copied source/code, model hashes and independent analysis.
    README specifies the artifact contract; no learner results are prefilled.
    """
    raise NotImplementedError("Реализуйте независимое сравнение pretrained моделей и submission")
