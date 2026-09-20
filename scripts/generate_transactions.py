"""Generate deterministic synthetic transaction datasets for the learning repository."""

from __future__ import annotations

import argparse
import csv
import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid5

Currency = Literal["EUR", "GBP", "MDL", "USD"]
TransactionStatus = Literal["approved", "declined", "pending", "refunded"]

FIELDNAMES: tuple[str, ...] = (
    "id",
    "user_id",
    "amount",
    "currency",
    "merchant",
    "category",
    "timestamp",
    "status",
    "is_fraud",
)
CURRENCIES: tuple[Currency, ...] = ("EUR", "GBP", "MDL", "USD")
STATUSES: tuple[TransactionStatus, ...] = (
    "approved",
    "declined",
    "pending",
    "refunded",
)
MERCHANT_CATEGORIES: tuple[tuple[str, str], ...] = (
    ("Aurora Market", "groceries"),
    ("Bluebird Travel", "travel"),
    ("Cedar Pharmacy", "health"),
    ("Delta Devices", "electronics"),
    ("Ember Energy", "utilities"),
    ("Fjord Books", "education"),
    ("Granite Fitness", "fitness"),
    ("Harbor Crypto", "digital_assets"),
)
TRANSACTION_NAMESPACE = UUID("912db270-32a0-55f6-a380-233fa83b061b")
START_AT = datetime(2025, 1, 1, tzinfo=UTC)
GENERATION_WINDOW_SECONDS = 180 * 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class GeneratedTransaction:
    """One entirely synthetic transaction ready for stable CSV serialization."""

    id: str
    user_id: str
    amount: Decimal
    currency: Currency
    merchant: str
    category: str
    timestamp: datetime
    status: TransactionStatus
    is_fraud: bool


def generate_transactions(*, seed: int, count: int) -> list[GeneratedTransaction]:
    """Return *count* deterministic synthetic transactions generated from *seed*."""
    if count < 0:
        raise ValueError("count must be non-negative")

    random_source = random.Random(seed)
    transactions: list[GeneratedTransaction] = []
    for index in range(count):
        merchant, category = random_source.choice(MERCHANT_CATEGORIES)
        amount = (Decimal(random_source.randint(199, 250_000)) / Decimal(100)).quantize(
            Decimal("0.01")
        )
        currency = random_source.choice(CURRENCIES)
        status = random_source.choices(
            STATUSES,
            weights=(0.87, 0.08, 0.03, 0.02),
            k=1,
        )[0]
        timestamp_offset = random_source.randrange(GENERATION_WINDOW_SECONDS)
        timestamp = START_AT + timedelta(seconds=timestamp_offset)
        risk_probability = _fraud_probability(
            amount=amount,
            currency=currency,
            merchant=merchant,
            status=status,
        )
        transactions.append(
            GeneratedTransaction(
                id=str(uuid5(TRANSACTION_NAMESPACE, f"{seed}:{index}")),
                user_id=f"user-{random_source.randrange(1, 251):04d}",
                amount=amount,
                currency=currency,
                merchant=merchant,
                category=category,
                timestamp=timestamp,
                status=status,
                is_fraud=random_source.random() < risk_probability,
            )
        )

    return sorted(transactions, key=lambda item: (item.timestamp, item.id))


def write_datasets(
    output_dir: Path,
    *,
    seed: int = 20260919,
    count: int = 1000,
) -> tuple[Path, Path]:
    """Write clean and intentionally dirty deterministic CSV datasets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_path = output_dir / "transactions.csv"
    dirty_path = output_dir / "transactions_dirty.csv"

    transactions = generate_transactions(seed=seed, count=count)
    clean_rows = [_serialize(transaction) for transaction in transactions]
    dirty_rows = _build_dirty_rows(seed)
    _write_csv(clean_path, clean_rows)
    _write_csv(dirty_path, dirty_rows)
    return clean_path, dirty_path


def _fraud_probability(
    *,
    amount: Decimal,
    currency: Currency,
    merchant: str,
    status: TransactionStatus,
) -> float:
    probability = 0.0008
    if merchant == "Harbor Crypto":
        probability += 0.008
    if amount >= Decimal("2000.00"):
        probability += 0.004
    if currency in {"GBP", "USD"}:
        probability += 0.001
    if status == "declined":
        probability += 0.003
    return probability


def _serialize(transaction: GeneratedTransaction) -> dict[str, str]:
    return {
        "id": transaction.id,
        "user_id": transaction.user_id,
        "amount": f"{transaction.amount:.2f}",
        "currency": transaction.currency,
        "merchant": transaction.merchant,
        "category": transaction.category,
        "timestamp": transaction.timestamp.isoformat(timespec="seconds"),
        "status": transaction.status,
        "is_fraud": str(transaction.is_fraud).lower(),
    }


def _build_dirty_rows(seed: int) -> list[dict[str, str]]:
    base_rows = [_serialize(item) for item in generate_transactions(seed=seed + 1, count=6)]
    exact_duplicate = base_rows[0].copy()
    reused_identifier = base_rows[1].copy()
    reused_identifier["amount"] = "999.99"
    invalid_amount = base_rows[2].copy()
    invalid_amount["amount"] = "not-a-decimal"
    invalid_timestamp = base_rows[3].copy()
    invalid_timestamp["timestamp"] = "not-a-timestamp"
    unknown_status = base_rows[4].copy()
    unknown_status["status"] = "unknown"
    missing_category = base_rows[5].copy()
    missing_category["category"] = ""
    return sorted(
        [
            base_rows[0],
            exact_duplicate,
            base_rows[1],
            reused_identifier,
            invalid_amount,
            invalid_timestamp,
            unknown_status,
            missing_category,
        ],
        key=lambda row: (row["timestamp"], row["id"], row["amount"]),
    )


def _write_csv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("datasets"))
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--count", type=int, default=1000)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the dataset generator CLI."""
    arguments = _parse_args(argv)
    clean_path, dirty_path = write_datasets(
        arguments.output,
        seed=arguments.seed,
        count=arguments.count,
    )
    print(f"Wrote {clean_path}")
    print(f"Wrote {dirty_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
