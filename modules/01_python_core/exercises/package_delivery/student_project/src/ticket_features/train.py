"""Student training adapter; reuse the package's single feature implementation."""

from collections.abc import Mapping, Sequence


def training_matrix(records: Sequence[Mapping[str, object]]) -> list[list[float]]:
    raise NotImplementedError("apply the shared ticket transform to every training record")
