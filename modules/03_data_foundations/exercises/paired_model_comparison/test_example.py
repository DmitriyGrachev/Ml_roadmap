"""The worked sensor example executes without learner code or network."""

import pytest

from .example import run_example
from .starter import DifferenceEstimate


def test_sensor_example_uses_per_sensor_means() -> None:
    result = run_example()
    assert result["effect"] == pytest.approx(-0.75)
    assert result["unit_count"] == 2
    assert result["resample_count"] == 200
    assert result == run_example()


@pytest.mark.parametrize("case", ["nonuniform", "unequal_clusters"])
def test_student_contract_rejects_no_bootstrap_mutant(
    case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from . import test_starter as contract

    effect, units, count = (5 / 3, 3, 150) if case == "nonuniform" else (3.0, 2, 100)

    def degenerate(*args: object, **kwargs: object) -> DifferenceEstimate:
        return DifferenceEstimate(effect, effect, effect, units, count)

    monkeypatch.setattr(contract, "paired_difference", degenerate)
    check = (
        contract.test_aligned_nonuniform_differences_and_seed_repeat
        if case == "nonuniform"
        else contract.test_unequal_cluster_sizes_get_equal_unit_weight
    )
    with pytest.raises(AssertionError):
        check()
