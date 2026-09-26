"""Student boundary for a chronological environmental-measurement split."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Measurement:
    """A uniquely timed environmental reading."""

    id: str
    observed_at: int
    value: float


@dataclass(frozen=True)
class TemporalSplit:
    """The retained train and test windows in chronological order."""

    train: tuple[Measurement, ...]
    test: tuple[Measurement, ...]


def chronological_split(
    measurements: tuple[Measurement, ...],
    *,
    train_size: int,
    test_size: int,
    gap: int = 0,
) -> TemporalSplit:
    """Sort by observation time and select windows under the README contract."""
    if type(train_size) is not int or train_size <= 0:
        raise ValueError("train_size must be a positive integer")
    if type(test_size) is not int or test_size <= 0:
        raise ValueError("test_size must be a positive integer")
    if type(gap) is not int or gap < 0:
        raise ValueError("gap must be a nonnegative integer")
    ids: set[str] = set()
    times: set[int] = set()
    for row in measurements:
        if not isinstance(row.id, str) or not row.id.strip() or row.id in ids:
            raise ValueError("measurement IDs must be nonblank and unique")
        if type(row.observed_at) is not int or row.observed_at in times:
            raise ValueError("observation times must be unique integers")
        if type(row.value) not in (int, float) or not isfinite(row.value):
            raise ValueError("measurement values must be finite numbers")
        ids.add(row.id)
        times.add(row.observed_at)
    if len(measurements) < train_size + gap + test_size:
        raise ValueError("not enough measurements for train, gap, and test windows")
    # TODO: select chronological windows without mutating the input.
    raise NotImplementedError("chronological split with a gap")
