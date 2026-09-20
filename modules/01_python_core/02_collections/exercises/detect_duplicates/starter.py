"""Student boundary for detecting duplicate transaction identifiers."""

from collections.abc import Iterable, Mapping


def find_duplicate_ids(transactions: Iterable[Mapping[str, object]]) -> set[str]:
    """Return transaction identifiers that appear more than once."""
    transaction_rows = list(transactions)
    for transaction in transaction_rows:
        transaction_id = transaction.get("id")
        if not isinstance(transaction_id, str) or not transaction_id.strip():
            raise ValueError("transaction ID must be a nonblank string")

    raise NotImplementedError("find duplicate transaction IDs")
