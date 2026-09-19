"""Build deterministic chronological partitions for synthetic support documents."""

from __future__ import annotations

import pandas as pd


def chronological_document_split() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Sort documents by arrival time before returning train, validation, and test frames."""
    documents = pd.DataFrame(
        {
            "document_id": ["D-3", "D-1", "D-4", "D-2"],
            "received_at": pd.to_datetime(
                [
                    "2026-01-03T09:00:00Z",
                    "2026-01-01T09:00:00Z",
                    "2026-01-04T09:00:00Z",
                    "2026-01-02T09:00:00Z",
                ],
                utc=True,
            ),
        }
    ).sort_values("received_at", kind="stable")
    return (
        documents.iloc[:2].copy(),
        documents.iloc[2:3].copy(),
        documents.iloc[3:].copy(),
    )


def main() -> None:
    """Print deterministic chronological partition sizes."""
    train, validation, test = chronological_document_split()
    print({"train": len(train), "validation": len(validation), "test": len(test)})


if __name__ == "__main__":
    main()
