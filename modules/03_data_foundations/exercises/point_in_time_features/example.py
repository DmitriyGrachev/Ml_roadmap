"""One literal query illustrates boundary policy without a general join solution."""

import pandas as pd


def run_example() -> dict[str, object]:
    """The equal-time and future rows are intentionally large poison values."""
    events = pd.DataFrame(
        {
            "event_id": ["before", "left", "inside", "same", "future"],
            "time": pd.to_datetime(
                ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
                utc=True,
            ),
            "amount": [1000.0, 5.0, 7.0, 10000.0, 100000.0],
        }
    )
    as_of = pd.Timestamp("2026-01-04", tz="UTC")
    included = events.loc[
        (events["time"] >= as_of - pd.Timedelta(days=2)) & (events["time"] < as_of)
    ]
    return {
        "event_ids": included["event_id"].tolist(),
        "count": len(included),
        "sum": float(included["amount"].sum()),
        "mean": float(included["amount"].mean()),
    }


if __name__ == "__main__":
    print(run_example())
