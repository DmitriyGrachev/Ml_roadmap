"""Test evaluation arithmetic without calling or grading a live model."""

from decimal import Decimal

import pytest

from roadmap_tools import exercise_call

from .starter import Case, Prediction, evaluate_answers


def test_joins_by_id_and_reports_quality_latency_and_decimal_cost() -> None:
    cases = (Case("a", "Monday"), Case("b", None), Case("c", "Atlas"), Case("d", None))
    predictions = (
        Prediction("d", "Probably", 20.0, Decimal("0.002")),
        Prediction("a", " monday ", 10.0, Decimal("0.001")),
        Prediction("c", "Encyclopedia", 30.0, Decimal("0.003")),
        Prediction("b", None, 100.0, Decimal("0.004")),
    )
    result = exercise_call(evaluate_answers, cases, predictions)
    assert result.total == 4
    assert result.correct == 2
    assert result.accuracy == 0.5
    assert result.answer_accuracy == 0.5
    assert result.refusal_accuracy == 0.5
    assert result.mean_latency_ms == 40.0
    assert result.p95_latency_ms == 100.0
    assert result.total_cost == Decimal("0.010")


def test_missing_refusal_slice_is_none_and_wrong_refusal_is_incorrect() -> None:
    result = exercise_call(
        evaluate_answers,
        (Case("a", "Atlas"),),
        (Prediction("a", None, 0.0, Decimal("0")),),
    )
    assert result.correct == 0
    assert result.answer_accuracy == 0.0
    assert result.refusal_accuracy is None


def test_all_refusals_and_single_record_percentile() -> None:
    result = exercise_call(
        evaluate_answers, (Case("a", None),), (Prediction("a", None, 7.0, Decimal("0.1")),)
    )
    assert result.accuracy == 1.0
    assert result.answer_accuracy is None
    assert result.refusal_accuracy == 1.0
    assert result.p95_latency_ms == 7.0


def test_p95_uses_nearest_rank_not_maximum_or_interpolation() -> None:
    cases = tuple(Case(str(i), "book") for i in range(20))
    predictions = tuple(
        Prediction(str(i), "BOOK", float(i + 1), Decimal("0.01")) for i in range(20)
    )
    result = exercise_call(evaluate_answers, cases, predictions)
    assert result.p95_latency_ms == 19.0
    assert result.mean_latency_ms == 10.5
    assert result.total_cost == Decimal("0.20")


def test_unicode_casefold_but_not_internal_whitespace_normalization() -> None:
    result = exercise_call(
        evaluate_answers,
        (Case("a", "Straße"), Case("b", "two words")),
        (
            Prediction("a", "STRASSE", 1.0, Decimal(0)),
            Prediction("b", "two  words", 1.0, Decimal(0)),
        ),
    )
    assert result.correct == 1


@pytest.mark.parametrize(
    ("cases", "predictions"),
    [
        ((), ()),
        ((Case("a", "x"),), ()),
        ((Case("a", "x"),), (Prediction("b", "x", 1.0, Decimal(0)),)),
        ((Case("a", "x"), Case("a", "y")), (Prediction("a", "x", 1.0, Decimal(0)),)),
        (
            (Case("a", "x"),),
            (Prediction("a", "x", 1.0, Decimal(0)), Prediction("a", "x", 1.0, Decimal(0))),
        ),
        ((Case(" ", "x"),), (Prediction(" ", "x", 1.0, Decimal(0)),)),
    ],
)
def test_rejects_empty_or_non_bijective_id_sets(
    cases: tuple[Case, ...], predictions: tuple[Prediction, ...]
) -> None:
    with pytest.raises(ValueError, match=r"case|prediction|identifier|ID"):
        exercise_call(evaluate_answers, cases, predictions)


@pytest.mark.parametrize("latency", [-1.0, float("nan"), float("inf")])
def test_rejects_invalid_latency(latency: float) -> None:
    with pytest.raises(ValueError, match="latency"):
        exercise_call(
            evaluate_answers,
            (Case("a", "x"),),
            (Prediction("a", "x", latency, Decimal(0)),),
        )


@pytest.mark.parametrize("cost", [Decimal("-0.1"), Decimal("NaN"), Decimal("Infinity")])
def test_rejects_invalid_cost(cost: Decimal) -> None:
    with pytest.raises(ValueError, match="cost"):
        exercise_call(evaluate_answers, (Case("a", "x"),), (Prediction("a", "x", 1.0, cost),))


@pytest.mark.parametrize(("expected", "answer"), [(" ", "x"), ("x", "\n"), (None, "")])
def test_blank_text_is_invalid_not_an_implicit_refusal(
    expected: str | None, answer: str | None
) -> None:
    with pytest.raises(ValueError, match="answer"):
        exercise_call(
            evaluate_answers,
            (Case("a", expected),),
            (Prediction("a", answer, 1.0, Decimal(0)),),
        )
