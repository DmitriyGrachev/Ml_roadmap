"""Small synthetic support records, generated only by an explicit call."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def make_fixture(seed: int) -> pd.DataFrame:
    """Return 144 records for 48 fictional support accounts; no external data."""
    rng = np.random.default_rng(seed)
    size = 144
    group_effect = np.repeat(rng.normal(0, 0.5, 48), 3)
    length = rng.integers(20, 700, size).astype(float)
    contacts = rng.integers(0, 6, size)
    queue = rng.uniform(0, 45, size).round(2)
    channel = rng.choice(["chat", "email", "portal"], size)
    logit = -0.8 + contacts * 0.2 + (channel == "email") * 0.3 + group_effect
    outcome = (rng.random(size) < 1 / (1 + np.exp(-logit))).astype(int)
    length[::17] = np.nan
    return pd.DataFrame(
        {
            "row_id": [f"support-{i:03d}" for i in range(size)],
            "group_id": [f"account-{i // 3:02d}" for i in range(size)],
            "time_id": pd.date_range("2025-01-01", periods=size, freq="h").astype(str),
            "message_length": length,
            "prior_contacts": contacts,
            "queue_minutes": queue,
            "channel": channel,
            "outcome": outcome,
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate tiny local support data")
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8", newline="") as destination:
        make_fixture(args.seed).to_csv(destination, index=False)
