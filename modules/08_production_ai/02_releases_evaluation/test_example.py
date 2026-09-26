"""Check deterministic manifest identity and an explicit holdout boundary."""

import pytest

from .example import evaluation_manifest, main


def test_manifest_is_order_independent_and_changes_with_case_membership() -> None:
    first = evaluation_manifest(frozenset({"dev"}), frozenset({"b", "a"}))
    assert first == evaluation_manifest(frozenset({"dev"}), frozenset({"a", "b"}))
    assert first.dataset_sha256 != evaluation_manifest(frozenset(), frozenset({"a"})).dataset_sha256
    assert len(first.dataset_sha256) == 64


@pytest.mark.parametrize("holdout", [frozenset(), frozenset({"dev"})])
def test_empty_or_contaminated_holdout_is_rejected(holdout: frozenset[str]) -> None:
    with pytest.raises(ValueError, match="holdout"):
        evaluation_manifest(frozenset({"dev"}), holdout)


def test_example_is_repeatable(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    first = capsys.readouterr().out
    main()
    assert capsys.readouterr().out == first
