"""Correct but deliberately non-Pythonic transaction grouping."""

from collections.abc import Iterable
from decimal import Decimal
from typing import TypedDict


class TransactionRow(TypedDict):
    """Transaction fields retained in each output group."""

    id: str
    user_id: str
    amount: Decimal
    currency: str
    status: str


def group_transactions(rows: Iterable[TransactionRow]) -> dict[str, list[TransactionRow]]:
    """Group transactions by user in first-seen order."""
    source_rows = list(rows)
    user_ids: list[str] = []
    grouped_rows: list[list[TransactionRow]] = []

    row_index = 0
    while row_index < len(source_rows):
        row = source_rows[row_index]
        group_found = False
        group_index = 0

        while group_index < len(user_ids):
            if user_ids[group_index] == row["user_id"]:
                grouped_rows[group_index].append(row.copy())
                group_found = True
            group_index += 1

        if not group_found:
            user_ids.append(row["user_id"])
            grouped_rows.append([row.copy()])

        row_index += 1

    result: dict[str, list[TransactionRow]] = {}
    result_index = 0
    while result_index < len(user_ids):
        result[user_ids[result_index]] = grouped_rows[result_index]
        result_index += 1

    return result
