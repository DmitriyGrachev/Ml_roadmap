"""Student inference adapter; feature order and normalization must match training."""

from collections.abc import Mapping


def serving_vector(record: Mapping[str, object]) -> list[float]:
    raise NotImplementedError("use the shared ticket transform for inference")
