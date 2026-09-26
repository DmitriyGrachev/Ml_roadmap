"""Select candidate prompt variants against a three-part acceptance policy."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TrialSummary:
    name: str
    quality: float
    p95_latency_ms: float
    cost_per_case: Decimal


def eligible_variants(
    summaries: tuple[TrialSummary, ...],
    quality_floor: float,
    latency_ceiling_ms: float,
    cost_ceiling: Decimal,
) -> tuple[str, ...]:
    """Filter already-validated trial summaries using an explicit release policy."""
    return tuple(
        item.name
        for item in summaries
        if item.quality >= quality_floor
        and item.p95_latency_ms <= latency_ceiling_ms
        and item.cost_per_case <= cost_ceiling
    )


def main() -> None:
    summaries = (
        TrialSummary("short-prompt", 0.80, 120.0, Decimal("0.002")),
        TrialSummary("worked-example", 0.95, 180.0, Decimal("0.004")),
        TrialSummary("verbose-prompt", 0.96, 600.0, Decimal("0.008")),
    )
    print(eligible_variants(summaries, 0.90, 300.0, Decimal("0.005")))
    print("These are synthetic summaries, not measured performance of any model.")


if __name__ == "__main__":
    main()
