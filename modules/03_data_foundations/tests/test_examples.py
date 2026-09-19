"""Smoke and invariant checks for the Module 03 runnable examples."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import pytest

MODULE_ROOT = Path(__file__).resolve().parents[1]


def load_example(lesson: str) -> ModuleType:
    """Load a numeric lesson path under a unique name to avoid import collisions."""
    source = MODULE_ROOT / lesson / "example.py"
    assert source.is_file(), f"missing lesson module: {source}"

    module_name = f"data_foundations_{lesson}_example"
    specification = importlib.util.spec_from_file_location(module_name, source)
    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "lesson",
    [
        "01_numpy",
        "02_pandas_core",
        "03_data_quality",
        "04_practical_statistics",
        "05_splits_and_leakage",
        "06_fraud_metrics",
    ],
)
def test_each_example_has_a_deterministic_main(lesson: str) -> None:
    example = load_example(lesson)

    assert example.main() is None


def test_numpy_example_broadcasts_currency_conversion() -> None:
    example = load_example("01_numpy")

    converted = example.convert_support_costs()

    np.testing.assert_allclose(converted, np.array([[12.0, 9.0], [24.0, 18.0]]))


def test_pandas_example_uses_named_groupby_aggregations() -> None:
    example = load_example("02_pandas_core")

    summary = example.summarize_ticket_resolution()

    expected = pd.DataFrame(
        {
            "channel": ["chat", "email"],
            "ticket_count": [2, 2],
            "average_minutes": [11.0, 35.0],
        }
    )
    pd.testing.assert_frame_equal(summary.reset_index(drop=True), expected)


def test_data_quality_example_counts_duplicates_and_missing_values() -> None:
    example = load_example("03_data_quality")

    quality = example.inspect_document_quality()

    assert quality == {"duplicate_document_ids": 1, "missing_language": 1}


def test_statistics_example_uses_a_median_robust_to_an_outlier() -> None:
    example = load_example("04_practical_statistics")

    assert example.median_response_latency() == 11.0


def test_split_example_orders_records_chronologically() -> None:
    example = load_example("05_splits_and_leakage")

    train, validation, test = example.chronological_document_split()

    assert train["received_at"].max() <= validation["received_at"].min()
    assert validation["received_at"].max() <= test["received_at"].min()


def test_fraud_metrics_example_returns_confusion_matrix_counts() -> None:
    example = load_example("06_fraud_metrics")

    assert example.confusion_counts() == {
        "true_positive": 1,
        "false_positive": 1,
        "true_negative": 1,
        "false_negative": 1,
    }
