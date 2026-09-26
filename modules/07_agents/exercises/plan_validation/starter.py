"""Validate plan structure and authority without scheduling or running tools."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    capability: str
    dependencies: tuple[str, ...] = ()


def validate_plan(
    steps: tuple[PlanStep, ...], allowed_capabilities: frozenset[str], max_steps: int
) -> tuple[str, ...]:
    """Return declaration-order IDs after the complete validation in the README."""
    # TODO: Validate bounds, names, the dependency DAG, then application permissions.
    raise NotImplementedError("Implement museum tool plan validation")
