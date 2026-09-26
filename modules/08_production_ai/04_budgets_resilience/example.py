"""Deadline arithmetic with an injected monotonic clock; no waits or retries."""

import math
from collections.abc import Callable


def remaining_timeout(deadline: float, clock: Callable[[], float], cap: float) -> float:
    now = clock()
    if not all(math.isfinite(value) for value in (deadline, now, cap)) or cap <= 0:
        raise ValueError("deadline, clock and positive cap must be finite")
    remaining = deadline - now
    if remaining <= 0:
        raise TimeoutError("request deadline exhausted")
    return min(remaining, cap)


def main() -> None:
    print(
        {
            "first_stage_timeout": remaining_timeout(12.0, lambda: 10.0, 1.5),
            "later_stage_timeout": remaining_timeout(12.0, lambda: 11.8, 1.5),
        }
    )
    print("The adapter must enforce this timeout and propagate cancellation to actual work.")


if __name__ == "__main__":
    main()
