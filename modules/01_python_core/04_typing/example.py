"""Normalize labels supplied through a structural data protocol."""

from typing import Protocol


class LabelSource(Protocol):
    @property
    def labels(self) -> tuple[str, ...]: ...


class SupportTicket:
    def __init__(self, *labels: str) -> None:
        self._labels = labels

    @property
    def labels(self) -> tuple[str, ...]:
        return self._labels


def normalize_labels(source: LabelSource) -> tuple[str, ...]:
    normalized = {label.strip().lower() for label in source.labels if label.strip()}
    return tuple(sorted(normalized))


def main() -> None:
    ticket = SupportTicket(" Billing ", "urgent", "billing")
    print(", ".join(normalize_labels(ticket)))


if __name__ == "__main__":
    main()
