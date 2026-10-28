"""Expose the existing scalar example's trace; not a generic model-training lab."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from .example import gradient as scalar_gradient
from .example import loss as scalar_loss
from .example import step as scalar_step

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def descent_trace(rate: float, updates: int = 6) -> pd.DataFrame:
    """Record this one fixed calibration case, using the pre-existing scalar step."""
    coefficient = 0.7
    rows = []
    for iteration in range(updates + 1):
        prediction = 2.0 * coefficient
        rows.append(
            {
                "iteration": iteration,
                "coefficient": coefficient,
                "prediction": prediction,
                "residual": prediction - 3.0,
                "loss": scalar_loss(coefficient),
                "gradient": scalar_gradient(coefficient),
            }
        )
        coefficient = scalar_step(coefficient, rate)
    return pd.DataFrame(rows)


def derivative_checks() -> pd.DataFrame:
    """Central differences diagnose this differentiable scalar case, not every function."""
    coefficient = 0.7
    analytic = scalar_gradient(coefficient)
    rows = []
    for epsilon in (1e-2, 1e-6, 1e-12, 1e-16):
        numerical = (scalar_loss(coefficient + epsilon) - scalar_loss(coefficient - epsilon)) / (
            2 * epsilon
        )
        rows.append(
            {
                "epsilon": epsilon,
                "analytic": analytic,
                "numerical": numerical,
                "absolute_error": abs(numerical - analytic),
            }
        )
    return pd.DataFrame(rows)


def make_figure() -> Figure:
    """One landscape and one shared-scale loss history show three different rates."""
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    points = np.linspace(-0.5, 3.0, 141)
    axes[0].plot(
        points, [scalar_loss(float(point)) for point in points], color="#555555", label="Loss(a)"
    )
    for rate, color in ((0.05, "#267d96"), (0.25, "#7d4b97"), (0.3, "#a64b29")):
        trace = descent_trace(rate)
        first = trace.iloc[:2]
        axes[0].plot(
            first["coefficient"],
            first["loss"],
            marker="o",
            color=color,
            label=f"Первый шаг: rate={rate}",
        )
        axes[1].plot(
            trace["iteration"], trace["loss"], marker="o", color=color, label=f"rate={rate}"
        )
    axes[0].set(
        title="Функция потерь и первые шаги",
        xlabel="Коэффициент a, °C (параметр)",
        ylabel="Квадрат ошибки, °C²",
    )
    axes[1].set(
        title="Один старт a=0.7, разные размеры шага",
        xlabel="Номер обновления (0 — до обучения)",
        ylabel="Loss, °C² (линейная шкала)",
    )
    for ax in axes:
        ax.legend(fontsize=9)
    return figure


def export_demo(output: Path) -> None:
    """No overwrite, no fitted model: save the fixed scalar traces and diagnostic."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = make_figure()
    try:
        output.mkdir(parents=True, exist_ok=False)
        for rate in (0.05, 0.25, 0.3):
            descent_trace(rate).to_csv(output / f"trace_{rate}.csv", index=False)
        derivative_checks().to_csv(output / "derivative_checks.csv", index=False)
        figure.savefig(output / "descent.png", dpi=150)
        metadata = {
            "example": "existing-scalar-calibration-v1",
            "loss_formula": "(2*a - 3)**2",
            "fixed_feature": 2,
            "target": 3,
            "start": 0.7,
            "rates": [0.05, 0.25, 0.3],
            "updates": 6,
            "versions": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "matplotlib": matplotlib.__version__,
            },
        }
        (output / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New directory; enables opt-in PNG export")
    args = parser.parse_args()
    for rate in (0.05, 0.25, 0.3):
        print(f"rate={rate}")
        print(descent_trace(rate).to_string(index=False))
    print(derivative_checks().to_string(index=False))
    if args.output is not None:
        try:
            export_demo(args.output)
        except FileExistsError:
            parser.error("Output already exists; choose a new directory")
        except ModuleNotFoundError as error:
            if error.name and error.name.startswith("matplotlib"):
                parser.error("Install plots explicitly: uv sync --locked --group visualization")
            raise
        print(f"Saved teacher artifacts to {args.output}")


if __name__ == "__main__":
    main()
