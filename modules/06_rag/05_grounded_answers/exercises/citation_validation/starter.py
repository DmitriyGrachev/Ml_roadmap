"""Check reference integrity without claiming to evaluate semantic truth."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

type IssueCode = Literal[
    "unknown_claim",
    "unknown_chunk",
    "source_mismatch",
    "empty_quote",
    "quote_not_found",
    "duplicate_citation",
]


@dataclass(frozen=True)
class Evidence:
    chunk_id: str
    source_id: str
    text: str


@dataclass(frozen=True)
class Citation:
    claim_id: str
    chunk_id: str
    source_id: str
    quote: str


@dataclass(frozen=True)
class CitationIssue:
    citation_index: int
    code: IssueCode


@dataclass(frozen=True)
class CitationReport:
    valid: tuple[Citation, ...]
    issues: tuple[CitationIssue, ...]
    uncited_claims: tuple[str, ...]


def validate_citations(
    claim_ids: Sequence[str],
    evidence: Sequence[Evidence],
    citations: Sequence[Citation],
) -> CitationReport:
    """Validate exact references and quotes with deterministic error precedence.

    Evidence is already authorized and belongs to a fixed corpus revision.
    Passing this check never establishes semantic support or factual correctness.
    """
    # TODO: validate source metadata, classify references, collect uncited claims.
    raise NotImplementedError("Implement evidence citation validation")
