"""Behavior test for the mutable-default debugging fixture."""

import pytest

from .broken import append_audit_tag


@pytest.mark.xfail(reason="intentional broken starter", strict=False)
def test_default_audit_tags_are_isolated_between_calls() -> None:
    first_tags = append_audit_tag("screened")
    second_tags = append_audit_tag("settled")

    assert first_tags == ["screened"]
    assert second_tags == ["settled"]
