"""Small, fully worked support-ticket EDA; independent of student weather tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def ticket_sample() -> pd.DataFrame:
    """Extend the four Pandas-lesson tickets with explicitly fictional audit cases."""
    return pd.DataFrame(
        [
            ["S-101", "chat", "2026-01-01", "8", "1"],
            ["S-102", "email", "2026-01-01", "30", "5"],
            ["S-103", "chat", "2026-01-02", "14", "2"],
            ["S-104", "email", "2026-01-02", "40", "8"],
            ["S-105", "chat", "2026-01-03", None, "3"],
            ["S-106", "email", "2026-01-03", "120", "20"],
            ["S-107", "chat", "2026-01-04", "10", None],
            ["S-108", None, "2026-01-04", "20", "4"],
            ["S-109", "email", "bad-date", "16", "2"],
            ["S-110", "chat", "2026-01-05", "-3", "1"],
            ["S-104", "email", "2026-01-02", "40", "8"],
            ["S-111", "email", "2026-01-05", "bad", "6"],
        ],
        columns=["ticket_id", "channel", "opened_day", "resolution_minutes", "followup_minutes"],
    )


def prepare_tickets(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Audit this demo schema; retain partial records and report unresolved key conflicts."""
    duplicate = raw.duplicated()
    clean = raw.loc[~duplicate].copy().reset_index(drop=True)
    audit = {
        "raw_rows": len(raw),
        "exact_duplicate_extras": int(duplicate.sum()),
        "retained_rows": len(clean),
        "conflicting_ticket_rows": int(clean["ticket_id"].duplicated(keep=False).sum()),
        "missing_channel": int(clean["channel"].isna().sum()),
    }
    for column in ("resolution_minutes", "followup_minutes"):
        source = clean[column]
        numeric = pd.to_numeric(source, errors="coerce").astype("float64")
        valid = np.isfinite(numeric) & numeric.ge(0)
        audit[f"missing_{column}"] = int(source.isna().sum())
        audit[f"unparseable_{column}"] = int((source.notna() & numeric.isna()).sum())
        audit[f"invalid_{column}"] = int((numeric.notna() & ~valid).sum())
        clean[column] = numeric.where(valid)
    source_day = clean["opened_day"]
    dates = pd.to_datetime(source_day, format="%Y-%m-%d", errors="coerce", utc=True)
    audit["missing_opened_day"] = int(source_day.isna().sum())
    audit["unparseable_opened_day"] = int((source_day.notna() & dates.isna()).sum())
    clean["opened_day"] = dates
    return clean, audit


def analysis_tables(clean: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Select rows per question instead of globally dropping every partial record."""
    distribution = clean.loc[
        clean["resolution_minutes"].notna(), ["ticket_id", "resolution_minutes"]
    ]
    relationship = clean.dropna(subset=["resolution_minutes", "followup_minutes"])[
        ["ticket_id", "resolution_minutes", "followup_minutes"]
    ]
    groups = (
        clean.assign(channel=clean["channel"].fillna("(unknown)"))
        .groupby("channel", as_index=False, observed=True)
        .agg(
            mean_minutes=("resolution_minutes", "mean"),
            observations=("resolution_minutes", "count"),
        )
        .sort_values("channel")
        .reset_index(drop=True)
    )
    time = (
        clean.dropna(subset=["opened_day"])
        .groupby("opened_day", as_index=False)
        .agg(
            mean_minutes=("resolution_minutes", "mean"),
            observations=("resolution_minutes", "count"),
        )
        .sort_values("opened_day")
        .reset_index(drop=True)
    )
    return {
        "distribution": distribution,
        "relationship": relationship,
        "groups": groups,
        "time": time,
    }


def make_figures(tables: dict[str, pd.DataFrame]) -> dict[str, Figure]:
    """Use explicit Figure/Axes; imports are opt-in, not needed for table inspection."""
    import matplotlib.pyplot as plt

    figures: dict[str, Figure] = {}

    fig, ax = plt.subplots(figsize=(7, 4.5), layout="constrained")
    ax.hist(
        tables["distribution"]["resolution_minutes"],
        bins=list(range(0, 141, 20)),
        color="#267d96",
        edgecolor="white",
        label="Наблюдаемые длительности",
    )
    ax.set(
        title=f"Распределение времени решения (n={len(tables['distribution'])})",
        xlabel="Время решения, мин",
        ylabel="Число обращений",
    )
    ax.legend()
    figures["distribution"] = fig

    pairs = tables["relationship"]
    fig, ax = plt.subplots(figsize=(7, 4.5), layout="constrained")
    ax.scatter(
        pairs["resolution_minutes"],
        pairs["followup_minutes"],
        color="#267d96",
        label="Измерения доступны попарно",
        s=55,
    )
    ax.set(
        title=f"Два измерения одного обращения (n={len(pairs)})",
        xlabel="Время решения, мин",
        ylabel="Дополнительная обработка, мин",
    )
    ax.legend()
    figures["relationship"] = fig

    groups = tables["groups"]
    fig, ax = plt.subplots(figsize=(7, 4.5), layout="constrained")
    bars = ax.bar(groups["channel"], groups["mean_minutes"], color="#267d96", label="Среднее")
    ax.bar_label(bars, labels=[f"n={n}" for n in groups["observations"]], padding=4)
    ax.set(
        title="Каналы: среднее и число доступных измерений",
        xlabel="Канал обращения",
        ylabel="Среднее время решения, мин",
    )
    ax.margins(y=0.25)
    ax.legend()
    figures["groups"] = fig

    time = tables["time"]
    fig, ax = plt.subplots(figsize=(7, 4.5), layout="constrained")
    ax.plot(
        time["opened_day"],
        time["mean_minutes"],
        marker="o",
        color="#267d96",
        label="Среднее по дню открытия",
    )
    ax.set_xticks(time["opened_day"], labels=time["opened_day"].dt.strftime("%d.%m.%Y").tolist())
    ax.set(
        title="Среднее по дню открытия (UTC)",
        xlabel="Дата открытия, UTC",
        ylabel="Среднее время решения, мин",
    )
    ax.text(
        0.02,
        0.97,
        "n по дням: " + ", ".join(str(n) for n in time["observations"]),
        transform=ax.transAxes,
        va="top",
        fontsize=9,
    )
    ax.margins(y=0.3)
    ax.legend(loc="upper right", bbox_to_anchor=(1, 0.85))
    figures["time"] = fig
    return figures


def export_demo(output: Path) -> dict[str, int]:
    """Save a fresh artifact directory, including inputs and numerical plot sources."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw = ticket_sample()
    clean, audit = prepare_tickets(raw)
    tables = analysis_tables(clean)
    figures = make_figures(tables)
    try:
        output.mkdir(parents=True, exist_ok=False)
        raw_text = raw.to_csv(index=False, lineterminator="\n")
        (output / "raw.csv").write_text(raw_text, encoding="utf-8")
        clean.to_csv(output / "prepared.csv", index=False)
        for name, figure in figures.items():
            figure.savefig(output / f"{name}.png", dpi=150)
            tables[name].to_csv(output / f"{name}.csv", index=False)
        metadata = {
            "dataset": "fictional-support-tickets-v1",
            "source_sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            "versions": {
                "python": platform.python_version(),
                "pandas": pd.__version__,
                "matplotlib": matplotlib.__version__,
            },
            "audit": audit,
            "policy": "exact duplicates removed; invalid fields masked; rows selected per question",
        }
        (output / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        for figure in figures.values():
            plt.close(figure)
    return audit


def main() -> None:
    """Explicitly create teacher charts; never run at import or during dependency sync."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory (must not exist)")
    args = parser.parse_args()
    try:
        audit = export_demo(args.output)
    except ModuleNotFoundError as error:
        if error.name and error.name.startswith("matplotlib"):
            parser.error("Install optional plotting dependencies: uv sync --group visualization")
        raise
    except FileExistsError:
        parser.error("Output already exists; choose a new directory to preserve previous work")
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    print(f"Saved 4 charts, input/prepared tables, plot tables and metadata to {args.output}")


if __name__ == "__main__":
    main()
