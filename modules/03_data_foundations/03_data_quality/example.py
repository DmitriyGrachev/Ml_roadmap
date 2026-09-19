"""Inspect duplicate and missing metadata in a synthetic document batch."""

from __future__ import annotations

import pandas as pd


def inspect_document_quality() -> dict[str, int]:
    """Count duplicate document IDs and missing language values."""
    documents = pd.DataFrame(
        {
            "document_id": ["D-201", "D-202", "D-203", "D-203"],
            "language": ["en", None, "ro", "ro"],
        }
    )
    return {
        "duplicate_document_ids": int(documents["document_id"].duplicated().sum()),
        "missing_language": int(documents["language"].isna().sum()),
    }


def main() -> None:
    """Print the deterministic document quality counts."""
    print(inspect_document_quality())


if __name__ == "__main__":
    main()
