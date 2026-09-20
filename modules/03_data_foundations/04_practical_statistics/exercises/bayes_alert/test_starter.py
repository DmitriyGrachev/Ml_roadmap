"""Acceptance tests for the Bayesian alert student boundary."""

from __future__ import annotations

import math

import pytest

from roadmap_tools import exercise_call

from .starter import fraud_probability_given_alert


def test_calculates_the_posterior_for_a_rare_fraud_event() -> None:
    posterior = exercise_call(
        fraud_probability_given_alert,
        base_rate=0.001,
        sensitivity=0.95,
        false_positive_rate=0.01,
    )

    assert posterior == pytest.approx(0.08683729433272395)


def test_rejects_zero_total_alert_probability() -> None:
    with pytest.raises(ValueError, match=r"alert|undefined|zero"):
        exercise_call(
            fraud_probability_given_alert,
            base_rate=0.0,
            sensitivity=0.0,
            false_positive_rate=0.0,
        )


@pytest.mark.parametrize("invalid", [-0.01, 1.01, math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("argument", ["base_rate", "sensitivity", "false_positive_rate"])
def test_rejects_invalid_probability_inputs(argument: str, invalid: float) -> None:
    probabilities = {
        "base_rate": 0.001,
        "sensitivity": 0.95,
        "false_positive_rate": 0.01,
    }
    probabilities[argument] = invalid

    with pytest.raises(ValueError, match=r"probability|finite|\[0, 1\]"):
        exercise_call(fraud_probability_given_alert, **probabilities)
