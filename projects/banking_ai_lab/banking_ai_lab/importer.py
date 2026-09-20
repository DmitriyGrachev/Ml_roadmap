"""Stage 1 infrastructure and the student-owned CSV import boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from banking_ai_lab.domain import Transaction


@dataclass(frozen=True, slots=True)
class ImportIssue:
    """One safe, field-specific CSV validation issue."""

    row_number: int
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Immutable valid transactions and ordered import issues."""

    transactions: tuple[Transaction, ...]
    issues: tuple[ImportIssue, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "transactions", tuple(self.transactions))
        object.__setattr__(self, "issues", tuple(self.issues))


def import_transactions(path: Path) -> ImportResult:
    """Import valid CSV rows and collect safe ordered issues without aborting."""
    if not path.is_file():
        raise FileNotFoundError(path)
    raise NotImplementedError("import and validate transaction CSV rows")
