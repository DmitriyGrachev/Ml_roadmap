"""A deterministic pre-step check illustrates count and elapsed-time limits."""

from typing import Literal


def stop_reason(
    model_turns: int, max_turns: int, elapsed_ms: int, deadline_ms: int
) -> Literal["turn_limit", "deadline"] | None:
    """Check already-validated counters before starting another model turn."""
    if elapsed_ms >= deadline_ms:
        return "deadline"
    if model_turns >= max_turns:
        return "turn_limit"
    return None


def main() -> None:
    for elapsed in (80, 100):
        print(f"elapsed={elapsed}: {stop_reason(2, 3, elapsed, 100)}")
    print("A pre-step deadline check does not interrupt an already-running tool.")


if __name__ == "__main__":
    main()
