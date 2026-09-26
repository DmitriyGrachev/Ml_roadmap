"""Stage budgets shrink under a shared request deadline."""

import pytest

from .example import main, remaining_timeout


def test_shared_deadline_caps_each_stage_and_rejects_exhaustion() -> None:
    assert remaining_timeout(12.0, lambda: 10.0, 1.5) == 1.5
    assert remaining_timeout(12.0, lambda: 11.8, 1.5) == pytest.approx(0.2)
    with pytest.raises(TimeoutError, match="deadline"):
        remaining_timeout(12.0, lambda: 12.0, 1.5)
    with pytest.raises(ValueError, match="finite"):
        remaining_timeout(12.0, lambda: 10.0, float("inf"))


def test_example_is_repeatable(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    first = capsys.readouterr().out
    main()
    assert capsys.readouterr().out == first
