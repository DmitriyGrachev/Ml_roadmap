"""Pass a notification callback as a regular Python value."""

from collections.abc import Callable

Notifier = Callable[[str], str]


def notify(message: str, formatter: Notifier) -> str:
    return formatter(message)


def main() -> None:
    print(notify("document indexed", lambda message: f"NOTICE: {message}"))


if __name__ == "__main__":
    main()
