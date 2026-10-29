"""Serving adapter; no duplicated preprocessing logic."""

from collections.abc import Mapping

from .transform import transform


def serving_vector(record: Mapping[str, object]) -> list[float]:
    return transform(record)
