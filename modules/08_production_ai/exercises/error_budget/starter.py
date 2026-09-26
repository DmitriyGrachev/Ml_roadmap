"""Summarize complete windows without treating partial or missing data as success."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

type NoDataPolicy = Literal["allow", "block"]


@dataclass(frozen=True)
class MeasurementWindow:
    window_id: str
    requests: int
    failures: int
    complete: bool


@dataclass(frozen=True)
class BudgetSummary:
    complete_windows: int
    requests: int
    failures: int
    allowed_failures: int
    remaining_failures: int
    can_release: bool


def summarize_error_budget(
    windows: tuple[MeasurementWindow, ...], target: Decimal, no_data: NoDataPolicy
) -> BudgetSummary:
    """Validate all windows and compute the integer failure allowance in the README."""
    # TODO: Aggregate complete windows, apply the target, and handle zero traffic explicitly.
    raise NotImplementedError("Implement catalog service error-budget accounting")
