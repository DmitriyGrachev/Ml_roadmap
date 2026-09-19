"""Summarize support-ticket resolution times with named Pandas aggregations."""

from __future__ import annotations

import pandas as pd


def summarize_ticket_resolution() -> pd.DataFrame:
    """Return a deterministic channel-level summary for synthetic support tickets."""
    tickets = pd.DataFrame(
        {
            "ticket_id": ["S-101", "S-102", "S-103", "S-104"],
            "channel": ["chat", "email", "chat", "email"],
            "resolution_minutes": [8.0, 30.0, 14.0, 40.0],
        }
    )
    return (
        tickets.groupby("channel", as_index=False)
        .agg(
            ticket_count=("ticket_id", "count"),
            average_minutes=("resolution_minutes", "mean"),
        )
        .sort_values("channel")
        .reset_index(drop=True)
    )


def main() -> None:
    """Print the deterministic ticket summary."""
    print(summarize_ticket_resolution())


if __name__ == "__main__":
    main()
