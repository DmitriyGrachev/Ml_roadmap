from __future__ import annotations

import csv
import importlib.util
import re
import subprocess
import sys
from collections import Counter
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import ModuleType
from uuid import UUID, uuid5

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPOSITORY_ROOT / "scripts" / "generate_transactions.py"
DATASET_DIRECTORY = REPOSITORY_ROOT / "datasets"
HEADER = [
    "id",
    "user_id",
    "amount",
    "currency",
    "merchant",
    "category",
    "timestamp",
    "status",
    "is_fraud",
]
SUPPORTED_CURRENCIES = {"EUR", "GBP", "MDL", "USD"}
SUPPORTED_STATUSES = {"approved", "declined", "pending", "refunded"}
FORBIDDEN_PERSONAL_COLUMNS = {
    "name",
    "email",
    "account_number",
    "card_number",
    "phone",
    "address",
}
EXPECTED_NAMESPACE = UUID("912db270-32a0-55f6-a380-233fa83b061b")


def load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("roadmap_transaction_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader.fieldnames or ()), list(reader)


def is_valid_amount(value: str) -> bool:
    try:
        amount = Decimal(value)
    except InvalidOperation:
        return False
    return amount > 0 and amount.as_tuple().exponent == -2


def is_valid_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0) and value.endswith("+00:00")


def test_generated_transaction_records_are_typed_frozen_and_deterministic() -> None:
    generator = load_generator()

    first = generator.generate_transactions(seed=17, count=8)
    second = generator.generate_transactions(seed=17, count=8)
    different_seed = generator.generate_transactions(seed=18, count=8)

    assert first == second
    assert different_seed != first
    assert len(first) == 8
    assert {record.id for record in first} == {
        str(uuid5(EXPECTED_NAMESPACE, f"17:{index}")) for index in range(8)
    }
    assert {record.id for record in different_seed} == {
        str(uuid5(EXPECTED_NAMESPACE, f"18:{index}")) for index in range(8)
    }
    record = first[0]
    assert isinstance(record.amount, Decimal)
    assert record.timestamp.utcoffset() == timedelta(0)
    with pytest.raises(FrozenInstanceError):
        record.currency = "CAD"


def test_generation_rejects_a_negative_count() -> None:
    generator = load_generator()

    with pytest.raises(ValueError, match="count"):
        generator.generate_transactions(seed=17, count=-1)


def test_writes_identical_bytes_to_two_clean_directories(tmp_path: Path) -> None:
    generator = load_generator()
    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"
    first_directory.mkdir()
    sentinel = first_directory / "keep-me.txt"
    sentinel.write_bytes(b"unrelated learner file\n")

    first_paths = generator.write_datasets(first_directory)
    second_paths = generator.write_datasets(second_directory)

    assert tuple(path.name for path in first_paths) == (
        "transactions.csv",
        "transactions_dirty.csv",
    )
    assert first_paths[0].read_bytes() == second_paths[0].read_bytes()
    assert first_paths[1].read_bytes() == second_paths[1].read_bytes()
    assert b"\r\n" not in first_paths[0].read_bytes()
    assert b"\r\n" not in first_paths[1].read_bytes()
    assert sentinel.read_bytes() == b"unrelated learner file\n"


def test_checked_in_datasets_match_a_fresh_default_generation(tmp_path: Path) -> None:
    generator = load_generator()
    clean, dirty = generator.write_datasets(tmp_path)

    assert clean.read_bytes() == (DATASET_DIRECTORY / "transactions.csv").read_bytes()
    assert dirty.read_bytes() == (DATASET_DIRECTORY / "transactions_dirty.csv").read_bytes()


def test_clean_dataset_has_the_documented_schema_and_domain_values(tmp_path: Path) -> None:
    generator = load_generator()
    clean, _dirty = generator.write_datasets(tmp_path)
    header, rows = read_csv(clean)

    assert header == HEADER
    assert FORBIDDEN_PERSONAL_COLUMNS.isdisjoint(header)
    assert len(rows) == 1_000
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(UUID(row["id"]).version == 5 for row in rows)
    assert all(re.fullmatch(r"user-\d{4}", row["user_id"]) for row in rows)
    assert all(is_valid_amount(row["amount"]) for row in rows)
    assert all(is_valid_timestamp(row["timestamp"]) for row in rows)
    assert {row["currency"] for row in rows} == SUPPORTED_CURRENCIES
    assert {row["status"] for row in rows} == SUPPORTED_STATUSES
    assert len({row["merchant"] for row in rows}) >= 5
    assert len({row["category"] for row in rows}) >= 5
    assert {row["is_fraud"] for row in rows} == {"false", "true"}
    fraud_rate = sum(row["is_fraud"] == "true" for row in rows) / len(rows)
    assert 0.0005 <= fraud_rate <= 0.01
    assert [(row["timestamp"], row["id"]) for row in rows] == sorted(
        (row["timestamp"], row["id"]) for row in rows
    )


def test_dirty_dataset_contains_each_documented_fault_independently(tmp_path: Path) -> None:
    generator = load_generator()
    _clean, dirty = generator.write_datasets(tmp_path)
    header, rows = read_csv(dirty)
    raw_data_lines = dirty.read_text(encoding="utf-8").splitlines()[1:]

    assert header == HEADER
    assert FORBIDDEN_PERSONAL_COLUMNS.isdisjoint(header)
    rows_by_id: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        rows_by_id.setdefault(row["id"], []).append(row)
    exact_duplicate_ids = {
        identifier
        for identifier, group in rows_by_id.items()
        if len(group) > 1 and len({tuple(row.items()) for row in group}) == 1
    }
    distinct_duplicate_ids = {
        identifier
        for identifier, group in rows_by_id.items()
        if len(group) > 1 and len({tuple(row.items()) for row in group}) > 1
    }
    assert len(exact_duplicate_ids) == 1
    assert len(distinct_duplicate_ids) == 1
    assert exact_duplicate_ids.isdisjoint(distinct_duplicate_ids)
    for identifier in distinct_duplicate_ids:
        for row in rows_by_id[identifier]:
            assert is_valid_amount(row["amount"])
            assert is_valid_timestamp(row["timestamp"])
            assert row["status"] in SUPPORTED_STATUSES
            assert row["category"]
    assert any(count > 1 for count in Counter(raw_data_lines).values())
    assert any(
        not is_valid_amount(row["amount"])
        and is_valid_timestamp(row["timestamp"])
        and row["status"] in SUPPORTED_STATUSES
        and row["category"]
        for row in rows
    )
    assert any(
        is_valid_amount(row["amount"])
        and not is_valid_timestamp(row["timestamp"])
        and row["status"] in SUPPORTED_STATUSES
        and row["category"]
        for row in rows
    )
    assert any(
        is_valid_amount(row["amount"])
        and is_valid_timestamp(row["timestamp"])
        and row["status"] not in SUPPORTED_STATUSES
        and row["category"]
        for row in rows
    )
    assert any(
        is_valid_amount(row["amount"])
        and is_valid_timestamp(row["timestamp"])
        and row["status"] in SUPPORTED_STATUSES
        and row["category"] == ""
        for row in rows
    )


def test_cli_writes_the_requested_seed_and_count(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(GENERATOR_PATH),
            "--output",
            str(tmp_path),
            "--seed",
            "23",
            "--count",
            "12",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    header, rows = read_csv(tmp_path / "transactions.csv")
    assert header == HEADER
    assert len(rows) == 12
    assert (tmp_path / "transactions_dirty.csv").is_file()
