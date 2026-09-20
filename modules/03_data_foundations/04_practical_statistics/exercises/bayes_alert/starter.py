"""Starter boundary for a Bayesian fraud-alert calculation."""

from __future__ import annotations


def fraud_probability_given_alert(
    base_rate: float,
    sensitivity: float,
    false_positive_rate: float,
) -> float:
    """Return the posterior fraud probability given that an alert fired.

    Every argument must be a finite probability in ``[0, 1]``. Raise ``ValueError``
    when an argument is invalid or when the total probability of an alert is zero,
    because conditioning on an impossible alert is undefined.
    """
    raise NotImplementedError("Implement the Bayesian alert calculation")
