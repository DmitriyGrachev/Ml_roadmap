"""Stream log lines one at a time instead of building a list first."""

from collections.abc import Iterator


def stream_log_lines() -> Iterator[str]:
    yield "INFO document=terms parsed"
    yield "INFO document=policy indexed"


def main() -> None:
    print(" | ".join(stream_log_lines()))


if __name__ == "__main__":
    main()
