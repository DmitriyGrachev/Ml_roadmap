"""Known-sigma design checks; Monte Carlo success is not a unit-test oracle."""

import math
import runpy
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

DEMO = (
    Path(__file__).resolve().parents[3]
    / "modules/03_data_foundations/04_practical_statistics/experiment_demo.py"
)


def api() -> dict[str, Any]:
    assert DEMO.is_file(), "Experiment design teacher demo is not implemented"
    return runpy.run_path(str(DEMO))


def test_plan_counts_per_arm_and_detects_cost_of_smaller_effect() -> None:
    plan = api()["required_per_arm"]
    assert plan(sigma=1.0, mde=0.5) == 63
    assert plan(sigma=1.0, mde=0.25) == 252
    assert plan(sigma=1.0, mde=0.5, comparisons=5) == 94


def test_two_sided_power_includes_both_tails_and_null_size() -> None:
    power = api()["normal_power"]
    assert power(effect=0.0, sigma=1.0, n=63) == pytest.approx(0.05)
    assert power(effect=0.5, sigma=1.0, n=63) == pytest.approx(0.8013024, abs=1e-7)
    assert power(effect=-0.5, sigma=1.0, n=63) == power(effect=0.5, sigma=1.0, n=63)


def test_null_power_preserves_tiny_alpha_without_cdf_cancellation() -> None:
    assert api()["normal_power"](effect=0.0, sigma=1.0, n=63, alpha=1e-20) == pytest.approx(
        1e-20, rel=1e-12, abs=0.0
    )


def test_interval_and_pvalue_use_known_sigma_of_two_independent_groups() -> None:
    result = api()["normal_result"](effect=0.5, sigma=1.0, n=32)
    # SE = sqrt(2/32) = .25, z = 2; not sigma/sqrt(n).
    assert result.lower == pytest.approx(0.0100090038649865)
    assert result.upper == pytest.approx(0.9899909961350135)
    assert result.p_value == pytest.approx(0.0455002638963584)
    zero = api()["normal_result"](effect=0.0, sigma=1.0, n=32)
    assert zero.p_value == 1.0


def test_peeking_uses_cumulative_prefixes_of_the_same_units() -> None:
    path = api()["decision_path"]([[3.0, -3.0, 0.0, 0.0]], sigma=math.sqrt(0.5))
    np.testing.assert_array_equal(path, [[True, False, False, False]])


def test_simulation_repeats_without_global_rng_side_effects_or_seed_selection() -> None:
    simulate = api()["simulate"]
    state = np.random.get_state()
    result = simulate(seed=17, repeats=20, n=12)
    assert result == simulate(seed=17, repeats=20, n=12)
    after = np.random.get_state()
    np.testing.assert_array_equal(state[1], after[1])
    assert state[2:] == after[2:]
    assert all(0.0 <= rate <= 1.0 for rate in result.values())
    assert result["aa_peek"] >= result["aa_fixed"]
    assert result["ab_peek"] >= result["ab_fixed"]


def test_simulation_adds_effect_and_counts_paths_not_individual_looks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FixedNoise:
        def normal(self, loc: float, scale: float, size: tuple[int, int]) -> NDArray[np.float64]:
            return np.array([[3.0, -3.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]])

    # Control only the random source: first AA path has one early crossing,
    # neither crosses at the end; adding 2 makes both AB final Z scores 4.
    monkeypatch.setattr(np.random, "default_rng", lambda seed: FixedNoise())
    assert api()["simulate"](repeats=2, n=4, sigma=math.sqrt(0.5), effect=2.0) == {
        "aa_fixed": 0.0,
        "aa_peek": 0.5,
        "ab_fixed": 1.0,
        "ab_peek": 1.0,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sigma": 0.0},
        {"sigma": math.inf},
        {"mde": -0.1},
        {"mde": math.nan},
        {"alpha": 0.0},
        {"alpha": 1.0},
        {"power": 0.5},
        {"power": 1.0},
        {"comparisons": 0},
        {"comparisons": True},
    ],
)
def test_invalid_design_rejected(kwargs: dict[str, float | int]) -> None:
    config: dict[str, float | int] = {"sigma": 1.0, "mde": 0.5}
    config.update(kwargs)
    with pytest.raises(ValueError, match=r"."):
        api()["required_per_arm"](**config)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": -1},
        {"seed": True},
        {"n": 0},
        {"repeats": 0},
        {"n": 10001},
        {"n": 10000, "repeats": 5000},
        {"effect": math.nan},
    ],
)
def test_simulation_rejects_invalid_or_unbounded_work(kwargs: dict[str, float | int]) -> None:
    with pytest.raises(ValueError, match=r"."):
        api()["simulate"](**kwargs)


@pytest.mark.parametrize("differences", [[], [[1.0], [math.nan]], [1.0, 2.0]])
def test_path_requires_finite_two_dimensional_differences(differences: object) -> None:
    with pytest.raises(ValueError, match=r"."):
        api()["decision_path"](differences, sigma=1.0)
