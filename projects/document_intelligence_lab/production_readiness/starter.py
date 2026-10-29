"""Independent learner implementation. Do not import the author demo."""

from pathlib import Path
from typing import Any

from .transport import LifecycleTransport


def summarize_outcomes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Count all attempts; latency statistics use successful requests only."""
    raise NotImplementedError("Implement HTTP outcomes and measured latency summary")


def join_delayed_labels(
    predictions: list[dict[str, Any]], labels: list[dict[str, Any]], *, as_of: int
) -> dict[str, Any]:
    """Join unique request IDs using label availability at the cutoff."""
    raise NotImplementedError("Implement delayed-label coverage and quality")


def run_lifecycle(
    bundle_a: Path,
    bundle_b: Path,
    output: Path,
    *,
    requests: int = 12,
    concurrency: int = 3,
    transport: LifecycleTransport | None = None,
) -> Path:
    """Run existing app over TCP; save learner lifecycle.json + bundle references.

    Implement child startup/cleanup, bounded clients, invalid/deadline probes,
    restart, failed digest, rollback. Use LocalTransport by default and the injected
    transport for deterministic offline checks. See evidence.py and README.
    """
    raise NotImplementedError("Implement and explicitly run a real local TCP lifecycle")
