"""Student contract for one fixed, preregistered family of hypotheses."""

from collections.abc import Sequence


def bonferroni_rejections(p_values: Sequence[float], alpha: float = 0.05) -> tuple[int, ...]:
    """Return original zero-based indexes rejected at alpha / len(p_values)."""
    # TODO: validate the whole fixed family, then apply its shared threshold.
    raise NotImplementedError("control the preregistered hypothesis family")
