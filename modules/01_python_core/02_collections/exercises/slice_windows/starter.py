"""Student boundary for dividing transaction IDs into slice windows."""

from collections.abc import Sequence


def transaction_windows(transaction_ids: Sequence[str], size: int) -> list[tuple[str, ...]]:
    """Return consecutive tuple windows, including a final partial window."""
    if size <= 0:
        raise ValueError("size must be positive")
    for transaction_id in transaction_ids:
        if not isinstance(transaction_id, str) or not transaction_id.strip():
            raise ValueError("transaction ID must be a nonblank string")

    raise NotImplementedError("slice transaction ID windows")
