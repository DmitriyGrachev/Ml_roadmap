"""Verify the observable inputs used by the learner-facing assertions."""


def test_comparison_sequence_counts_value_comparisons() -> None:
    from .instrumentation import ComparisonSequence

    values = ComparisonSequence(range(4))
    assert len(values) == 4
    assert values[2] < 3
    assert values[2] == 2
    assert values.comparisons == 2


def test_one_shot_input_records_one_complete_iteration() -> None:
    from .instrumentation import OneShotValues

    values = OneShotValues([4, 1, 4])
    assert list(values) == [4, 1, 4]
    assert values.iterations == 1
    assert values.pulls == 3
