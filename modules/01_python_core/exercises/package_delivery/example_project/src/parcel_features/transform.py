"""Feature contract v1: kilograms and normalized destination character count."""

import math
from collections.abc import Mapping


def transform(record: Mapping[str, object]) -> list[float]:
    weight = record["weight_grams"]
    if (
        isinstance(weight, bool)
        or not isinstance(weight, int | float)
        or not math.isfinite(weight)
        or weight < 0
    ):
        raise ValueError("weight_grams must be a finite nonnegative number")
    destination = record["destination"]
    if not isinstance(destination, str):
        raise ValueError("destination must be text")
    normalized = " ".join(destination.split()).casefold()
    return [float(weight) / 1000.0, float(len(normalized))]
