"""Check exact source relationships and explicit limits of citation validation."""

import pytest

from roadmap_tools import exercise_call

from .starter import Citation, Evidence, validate_citations


def evidence_rows() -> list[Evidence]:
    return [
        Evidence("hours:r2:0", "north-library", "Open at 09:00. Café closes at 16:00."),
        Evidence("garden:r1:0", "garden", "Plants need shade."),
    ]


def test_accepts_exact_quotes_preserves_order_and_marks_only_uncited_claims() -> None:
    citations = [
        Citation("c2", "garden:r1:0", "garden", "Plants need shade."),
        Citation("c1", "hours:r2:0", "north-library", "Café closes"),
        Citation("c1", "hours:r2:0", "north-library", " at 09:00. "),
    ]
    before = citations.copy()
    report = exercise_call(validate_citations, ["c1", "c2", "c3"], evidence_rows(), citations)
    assert report.valid == tuple(citations)
    assert report.issues == ()
    assert report.uncited_claims == ("c3",)
    assert citations == before


def test_precedence_rejects_wrong_references_and_duplicates() -> None:
    first = Citation("c1", "hours:r2:0", "north-library", "Open")
    citations = [
        first,
        Citation("unknown", "missing", "wrong", ""),
        Citation("c2", "missing", "wrong", ""),
        Citation("c2", "hours:r2:0", "garden", ""),
        Citation("c2", "hours:r2:0", "north-library", "   "),
        Citation("c2", "hours:r2:0", "north-library", "Plants need shade."),
        first,
    ]
    report = exercise_call(validate_citations, ["c1", "c2"], evidence_rows(), citations)
    assert report.valid == (first,)
    assert [(issue.citation_index, issue.code) for issue in report.issues] == [
        (1, "unknown_claim"),
        (2, "unknown_chunk"),
        (3, "source_mismatch"),
        (4, "empty_quote"),
        (5, "quote_not_found"),
        (6, "duplicate_citation"),
    ]
    assert report.uncited_claims == ("c2",)


@pytest.mark.parametrize("quote", ["open", "Open  at", "Cafe", "Plants need shade."])
def test_matching_never_changes_case_whitespace_unicode_or_chunk(quote: str) -> None:
    citation = Citation("claim", "hours:r2:0", "north-library", quote)
    report = exercise_call(validate_citations, ["claim"], evidence_rows(), [citation])
    assert report.valid == ()
    assert report.issues[0].code == "quote_not_found"
    assert report.uncited_claims == ("claim",)


def test_an_exact_quote_is_structurally_valid_without_claim_semantics() -> None:
    # The checker receives a claim ID, not an assertion to infer or endorse.
    citation = Citation("claim-about-unrelated-topic", "garden:r1:0", "garden", "shade")
    report = exercise_call(validate_citations, [citation.claim_id], evidence_rows(), [citation])
    assert report.valid == (citation,)
    assert report.issues == ()


def test_empty_inputs_and_missing_evidence_are_explicit() -> None:
    empty = exercise_call(validate_citations, [], [], [])
    assert empty.valid == ()
    assert empty.issues == ()
    assert empty.uncited_claims == ()
    report = exercise_call(validate_citations, ["b", "a"], [], [])
    assert report.uncited_claims == ("b", "a")


@pytest.mark.parametrize("claims", [["a", "a"], [""], ["  "]])
def test_invalid_claim_declarations_are_rejected(claims: list[str]) -> None:
    with pytest.raises(ValueError, match="claim"):
        exercise_call(validate_citations, claims, [], [])


@pytest.mark.parametrize(
    "evidence",
    [
        [Evidence("same", "one", "x"), Evidence("same", "two", "y")],
        [Evidence("", "source", "text")],
        [Evidence("chunk", " ", "text")],
    ],
)
def test_invalid_evidence_metadata_is_rejected(evidence: list[Evidence]) -> None:
    with pytest.raises(ValueError, match="evidence"):
        exercise_call(validate_citations, [], evidence, [])
