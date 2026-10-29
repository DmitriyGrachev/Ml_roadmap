"""A fixed arithmetic example, explicitly not measured model performance."""

from statistics import median


def worked_example() -> dict[str, object]:
    """Demonstrate batch wall time vs sum of overlapping request durations."""
    successful_ms = [80.0, 120.0, 160.0]
    elapsed_s = 0.2
    return {
        "origin": "SYNTHETIC_ARITHMETIC_ONLY",
        "successful_requests_per_s": len(successful_ms) / elapsed_s,
        "median_success_latency_ms": median(successful_ms),
        "sum_request_durations_s": sum(successful_ms) / 1000,
        "batch_wall_s": elapsed_s,
        "empirical_p95": None,
    }


if __name__ == "__main__":
    print(worked_example())
