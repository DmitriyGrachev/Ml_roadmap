"""Student boundary: duration cap and normalized categorical priority."""

from collections.abc import Mapping


def transform(record: Mapping[str, object]) -> list[float]:
    """Return [min(duration_minutes, 120)/120, priority_code] after validation."""
    # TODO: validate finite nonnegative numeric duration (bool is invalid), normalize priority.
    raise NotImplementedError("implement ticket feature contract, distinct from parcel example")
