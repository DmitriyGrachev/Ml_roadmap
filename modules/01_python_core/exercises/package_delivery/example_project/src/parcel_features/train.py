"""Training adapter uses the same feature function as online inference."""

from collections.abc import Mapping, Sequence

from .transform import transform


def training_matrix(records: Sequence[Mapping[str, object]]) -> list[list[float]]:
    return [transform(record) for record in records]
