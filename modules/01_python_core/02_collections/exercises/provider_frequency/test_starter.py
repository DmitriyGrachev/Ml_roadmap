"""Tests for the provider-frequency student exercise."""

import pytest

from roadmap_tools import exercise_call

from .starter import provider_frequencies


@pytest.mark.student_exercise
def test_provider_frequencies_counts_in_first_seen_order_from_a_generator() -> None:
    providers = (provider for provider in ("Stripe", "Adyen", "Stripe", "Checkout"))

    assert list(exercise_call(provider_frequencies, providers).items()) == [
        ("Stripe", 2),
        ("Adyen", 1),
        ("Checkout", 1),
    ]


@pytest.mark.student_exercise
def test_provider_frequencies_returns_empty_mapping_for_empty_input() -> None:
    assert exercise_call(provider_frequencies, []) == {}


@pytest.mark.student_exercise
def test_provider_frequencies_keeps_mixed_case_names_distinct() -> None:
    assert exercise_call(provider_frequencies, ["Stripe", "stripe", "Stripe"]) == {
        "Stripe": 2,
        "stripe": 1,
    }
