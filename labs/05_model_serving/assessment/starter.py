"""Independent learner implementation; no network or server startup here."""

from collections.abc import Mapping, Sequence


def summarize_measurements(
    records: Sequence[Mapping[str, object]], *, elapsed_s: float
) -> dict[str, object]:
    """Compute the documented success/error, throughput and empirical timing summary."""
    raise NotImplementedError("Implement measurement arithmetic and explain its limits")
