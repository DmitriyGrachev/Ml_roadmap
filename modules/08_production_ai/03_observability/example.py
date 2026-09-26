"""A trace fixture distinguishes parallel child time from end-to-end latency."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    name: str
    start_ms: int
    end_ms: int

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


def museum_trace() -> tuple[Span, ...]:
    return (
        Span("request", 0, 150),
        Span("catalog", 10, 80),
        Span("permissions", 10, 50),
        Span("generate", 80, 145),
    )


def main() -> None:
    root, *children = museum_trace()
    print(
        {
            "trace_id": "fixture-001",
            "request_ms": root.duration_ms,
            "sum_child_ms": sum(child.duration_ms for child in children),
        }
    )
    print("Parallel spans overlap: adding their durations is not request latency.")


if __name__ == "__main__":
    main()
