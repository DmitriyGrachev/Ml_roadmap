"""Model a ledger entry as an immutable value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LedgerEntry:
    reference: str
    amount: Decimal
    currency: str


def main() -> None:
    entry = LedgerEntry("doc-42", Decimal("18.50"), "EUR")
    print(entry)


if __name__ == "__main__":
    main()
