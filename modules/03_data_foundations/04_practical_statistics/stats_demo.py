"""Fixed teacher statistics experiments; no student contracts or network data."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from numpy.typing import NDArray

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def latency_data() -> pd.DataFrame:
    """Reuse the lesson's unusual batch and change only its final observation."""
    return pd.DataFrame(
        {"base": [8.0, 10.0, 11.0, 14.0, 17.0], "unusual": [8.0, 10.0, 11.0, 14.0, 300.0]}
    )


def latency_comparison() -> pd.DataFrame:
    """Describe only these two fixed cases, not the student's generic profile."""
    data = latency_data()
    return pd.DataFrame(
        [
            {
                "case": name,
                "mean_minutes": float(np.mean(data[name])),
                "median_minutes": float(np.median(data[name])),
                "variance_minutes2": float(np.var(data[name], ddof=0)),
                "std_minutes": float(np.std(data[name], ddof=0)),
            }
            for name in ("base", "unusual")
        ]
    )


def library_frequencies() -> pd.DataFrame:
    """A fictional complete 100-visit table, not measured population probabilities."""
    return pd.DataFrame(
        {"membership": ["member", "nonmember"], "borrow": [30, 12], "no_borrow": [10, 48]}
    )


def library_probabilities() -> dict[str, float]:
    """Uniformly select one visit from this fixed table; expose each denominator."""
    counts = library_frequencies()[["borrow", "no_borrow"]].to_numpy(dtype=np.float64)
    joint = float(counts[0, 0])
    member = float(counts[0].sum())
    borrow = float(counts[:, 0].sum())
    total = float(counts.sum())
    return {
        "member": member / total,
        "borrow": borrow / total,
        "borrow_given_member": joint / member,
        "member_given_borrow": joint / borrow,
    }


def sampling_experiment(
    seed: int = 2026, repeats: int = 500
) -> tuple[dict[int, NDArray[np.float64]], pd.DataFrame]:
    """IID uniform draws WITH replacement from an explicitly known toy population."""
    if seed < 0 or repeats < 1:
        raise ValueError("seed must be nonnegative and repeats must be positive")
    population = latency_data()["base"].to_numpy(dtype=np.float64)
    rng = np.random.default_rng(seed)
    draws = {
        n: rng.choice(population, size=(repeats, n), replace=True).astype(np.float64)
        for n in (5, 50)
    }
    estimates = pd.concat(
        [
            pd.DataFrame(
                {
                    "n": n,
                    "repetition": np.arange(repeats),
                    "mean_minutes": samples.mean(axis=1),
                }
            )
            for n, samples in draws.items()
        ],
        ignore_index=True,
    )
    return draws, estimates


def make_figures(estimates: pd.DataFrame) -> dict[str, Figure]:
    """Separate observations from summaries and the distribution of sample means."""
    import matplotlib.pyplot as plt

    values = latency_data()
    summary = latency_comparison()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for name, label, color in (
        ("base", "Пятое значение: 17 мин", "#267d96"),
        ("unusual", "Пятое значение: 300 мин", "#a64b29"),
    ):
        axes[0].plot(range(1, 6), values[name], marker="o", label=label, color=color)
    axes[0].set(
        title="Наблюдения: меняем только пятое",
        xlabel="Номер наблюдения (не время)",
        ylabel="Длительность, мин",
        xticks=list(range(1, 6)),
    )
    positions = np.arange(3)
    for index, (label, color) in enumerate((("17 мин", "#267d96"), ("300 мин", "#a64b29"))):
        heights = summary.loc[index, ["mean_minutes", "median_minutes", "std_minutes"]].to_numpy(
            dtype=float
        )
        axes[1].bar(positions + (index - 0.5) * 0.36, heights, width=0.36, label=label, color=color)
    axes[1].set_xticks(positions, labels=["Среднее", "Медиана", "Станд. откл."])
    axes[1].set(title="Статистики этих пяти значений", xlabel="Показатель", ylabel="Минуты")
    for ax in axes:
        ax.legend()

    sampling, panels = plt.subplots(
        1, 2, figsize=(11, 4.5), sharex=True, sharey=True, layout="constrained"
    )
    largest_bin = 0.0
    for ax, n in zip(panels, (5, 50), strict=True):
        means = estimates.loc[estimates["n"].eq(n), "mean_minutes"]
        frequencies, _, _ = ax.hist(
            means, bins=np.linspace(8, 17, 19).tolist(), color="#267d96", label="Средние выборок"
        )
        largest_bin = max(largest_bin, float(np.max(frequencies)))
        ax.axvline(12, color="#a64b29", linestyle="--", label="Среднее совокупности: 12")
        ax.set(
            title=f"n={n}; повторов {len(means)}",
            xlabel="Оценка среднего, мин (не наблюдение)",
            ylabel="Число выборок в интервале",
        )
        ax.legend()
    # Shared headroom keeps the legend clear of the tallest histogram bars.
    panels[0].set_ylim(0, largest_bin * 1.45)
    return {"outlier": fig, "sampling": sampling}


def export_demo(output: Path, seed: int = 2026) -> None:
    """Write only to a new explicitly selected directory, with numerical plot sources."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    draws, estimates = sampling_experiment(seed)
    figures = make_figures(estimates)
    try:
        output.mkdir(parents=True, exist_ok=False)
        raw_csv = latency_data().to_csv(index=False, lineterminator="\n")
        (output / "latencies.csv").write_bytes(raw_csv.encode("utf-8"))
        latency_comparison().to_csv(output / "comparison.csv", index=False)
        library_frequencies().to_csv(output / "frequencies.csv", index=False)
        estimates.to_csv(output / "sample_means.csv", index=False)
        for n, samples in draws.items():
            pd.DataFrame(samples).to_csv(output / f"draws_n{n}.csv", index=False)
        for name, figure in figures.items():
            figure.savefig(output / f"{name}.png", dpi=150)
        metadata = {
            "dataset": "fictional-latencies-and-library-v1",
            "source_sha256": hashlib.sha256(raw_csv.encode("utf-8")).hexdigest(),
            "source_file": "latencies.csv",
            "seed": seed,
            "repeats": 500,
            "sample_sizes": [5, 50],
            "replace": True,
            "population_policy": "uniform IID draws from [8, 10, 11, 14, 17]",
            "ddof": 0,
            "ddof_scope": "latency comparison; printed sampling summary uses ddof=1",
            "probabilities": library_probabilities(),
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
        for figure in figures.values():
            plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New directory; enables opt-in PNG export")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if args.seed < 0:
        parser.error("seed must be nonnegative")
    print(latency_comparison().to_string(index=False))
    print(json.dumps(library_probabilities(), sort_keys=True))
    _, estimates = sampling_experiment(args.seed)
    print(estimates.groupby("n")["mean_minutes"].agg(["count", "mean", "std"]).to_string())
    print("Last std: spread of 500 estimates (ddof=1), NOT spread of individual observations.")
    if args.output is not None:
        try:
            export_demo(args.output, args.seed)
        except FileExistsError:
            parser.error("Output already exists; choose a new directory")
        except ModuleNotFoundError as error:
            if error.name and error.name.startswith("matplotlib"):
                parser.error("Install plots explicitly: uv sync --locked --group visualization")
            raise
        print(f"Saved teacher artifacts to {args.output}")


if __name__ == "__main__":
    main()
