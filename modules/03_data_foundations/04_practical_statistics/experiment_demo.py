"""Bounded known-sigma normal experiments, with a deliberately invalid peeking rule."""

import argparse
import math
from statistics import NormalDist
from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

NORMAL = NormalDist()


def _positive(value: float, name: str) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


def _count(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _critical(alpha: float) -> float:
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be finite and inside (0, 1)")
    # Lower-tail quantile avoids rounding 1 - alpha/2 to one for small alpha.
    return -NORMAL.inv_cdf(alpha / 2)


def required_per_arm(
    sigma: float, mde: float, alpha: float = 0.05, power: float = 0.8, comparisons: int = 1
) -> int:
    """Plan equal independent groups using the usual normal design approximation."""
    _positive(sigma, "sigma")
    _positive(mde, "mde")
    _count(comparisons, "comparisons")
    if not math.isfinite(power) or not 0.5 < power < 1:
        raise ValueError("power must be finite and inside (0.5, 1)")
    _critical(alpha)
    scale = math.sqrt(2) * (sigma / mde) * (_critical(alpha / comparisons) + NORMAL.inv_cdf(power))
    n = scale * scale
    if not math.isfinite(n):
        raise ValueError("design size must be finite")
    return max(1, math.ceil(n))


def normal_power(effect: float, sigma: float, n: int, alpha: float = 0.05) -> float:
    """Both tails of N(effect/SE, 1), exact for this known-sigma Gaussian model."""
    _positive(sigma, "sigma")
    _count(n, "n")
    if not math.isfinite(effect):
        raise ValueError("effect must be finite")
    shift = abs(effect) / (sigma * math.sqrt(2 / n))
    critical = _critical(alpha)
    return 0.5 * math.erfc((critical - shift) / math.sqrt(2)) + 0.5 * math.erfc(
        (critical + shift) / math.sqrt(2)
    )


class NormalResult(NamedTuple):
    lower: float
    upper: float
    p_value: float


def normal_result(effect: float, sigma: float, n: int, alpha: float = 0.05) -> NormalResult:
    """Fixed-horizon pointwise interval and two-sided p-value for B minus A."""
    _positive(sigma, "sigma")
    _count(n, "n")
    if not math.isfinite(effect):
        raise ValueError("effect must be finite")
    se = sigma * math.sqrt(2 / n)
    margin = _critical(alpha) * se
    p_value = math.erfc(abs(effect / se) / math.sqrt(2))
    return NormalResult(effect - margin, effect + margin, p_value)


def decision_path(differences: ArrayLike, sigma: float, alpha: float = 0.05) -> NDArray[np.bool_]:
    """Rows are independent repetitions; columns add one new unit to each arm."""
    _positive(sigma, "sigma")
    values = np.asarray(differences, dtype=np.float64)
    if (
        values.ndim != 2
        or 0 in values.shape
        or values.size > 2_000_000
        or not np.isfinite(values).all()
    ):
        raise ValueError("differences must be a finite nonempty 2D array, at most 2M cells")
    sizes = np.arange(1, values.shape[1] + 1)
    z = values.cumsum(axis=1) / (sigma * np.sqrt(2 * sizes))
    return np.asarray(np.abs(z) >= _critical(alpha), dtype=np.bool_)


def simulate(
    seed: int = 29,
    repeats: int = 2000,
    n: int = 63,
    sigma: float = 1.0,
    effect: float = 0.5,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Compare final-only and any-prefix rejection on the same generated paths."""
    _count(n, "n")
    _count(repeats, "repeats")
    _positive(sigma, "sigma")
    _critical(alpha)
    if (
        isinstance(seed, bool)
        or not isinstance(seed, int)
        or seed < 0
        or n > 10000
        or repeats > 5000
        or n * repeats > 2_000_000
        or not math.isfinite(effect)
    ):
        raise ValueError("invalid seed/effect or budget: n<=10000, repeats<=5000, cells<=2M")
    # Distribution identity: B_i - A_i ~ N(effect, 2*sigma**2).
    # Indices join two independent units, not two readings of the same subject.
    noise = np.random.default_rng(seed).normal(0, math.sqrt(2) * sigma, size=(repeats, n))
    rates: dict[str, float] = {}
    for label, shift in (("aa", 0.0), ("ab", effect)):
        rejected = decision_path(noise + shift, sigma, alpha)
        rates[f"{label}_fixed"] = float(rejected[:, -1].mean())
        rates[f"{label}_peek"] = float(rejected.any(axis=1).mean())
    return rates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument("--repeats", type=int, default=2000)
    parser.add_argument("--sigma", type=float, default=1.0)
    parser.add_argument("--mde", type=float, default=0.5)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.8)
    parser.add_argument("--comparisons", type=int, default=1)
    parser.add_argument("--n", type=int, help="override planned units per arm")
    args = parser.parse_args()
    planned = required_per_arm(args.sigma, args.mde, args.alpha, args.power, args.comparisons)
    n = planned if args.n is None else args.n
    per_test_alpha = args.alpha / args.comparisons
    rates = simulate(args.seed, args.repeats, n, args.sigma, args.mde, per_test_alpha)
    print(
        f"seed={args.seed} repeats={args.repeats} sigma={args.sigma:g} mde={args.mde:g} "
        f"alpha_family={args.alpha:g} comparisons={args.comparisons} target_power={args.power:g}"
    )
    print(f"planned_per_arm={planned} actual_per_arm={n} total_units={2 * n}")
    print(f"normal_power_at_mde={normal_power(args.mde, args.sigma, n, per_test_alpha):.6f}")
    print("scenario fixed_final any_prefix (the latter is an unadjusted peeking rule)")
    for label in ("aa", "ab"):
        print(f"{label.upper()} {rates[f'{label}_fixed']:.4f} {rates[f'{label}_peek']:.4f}")
    print("independent_null_tests unadjusted_family_risk")
    for comparisons in (1, 5, 20):
        print(f"{comparisons} {1 - (1 - args.alpha) ** comparisons:.6f}")


if __name__ == "__main__":
    main()
