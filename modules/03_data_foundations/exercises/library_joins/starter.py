"""Student boundary for a validated many-to-one library report join."""

import pandas as pd


def build_loan_report(books: pd.DataFrame, loans: pd.DataFrame) -> pd.DataFrame:
    """Return loan_id/title/days rows in loan order after validating keys and days."""
    # TODO: validate schema and keys, join with cardinality checks, and project a fresh report.
    raise NotImplementedError("report library loans")
