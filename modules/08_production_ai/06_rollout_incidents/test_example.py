"""Rollback requires both a retrievable artifact and compatible stored data."""

import pytest

from .example import Release, main, rollback_preflight


def test_rollback_requires_artifact_and_schema_compatibility() -> None:
    release = Release("v1", frozenset({1, 2}))
    assert rollback_preflight(release, 2, True)
    assert not rollback_preflight(release, 2, False)
    assert not rollback_preflight(release, 3, True)


def test_example_is_repeatable(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    first = capsys.readouterr().out
    main()
    assert capsys.readouterr().out == first
