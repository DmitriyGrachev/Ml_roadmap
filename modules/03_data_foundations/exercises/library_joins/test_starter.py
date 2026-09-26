"""Protect row counts, key meaning, caller data, and stable report ordering."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from roadmap_tools.exercise import exercise_call

from .starter import build_loan_report

pytestmark = pytest.mark.student_exercise


def catalog() -> pd.DataFrame:
    return pd.DataFrame({"book_id": ["b2", "b1"], "title": ["Clouds", "Trees"]})


def loans() -> pd.DataFrame:
    return pd.DataFrame(
        {"loan_id": ["l2", "l1", "l3"], "book_id": ["b1", "b2", "b1"], "days": [4, 0, 2]}
    )


def test_many_loans_to_one_book_preserve_loan_order_and_project_columns() -> None:
    result = exercise_call(build_loan_report, catalog(), loans())
    expected = pd.DataFrame(
        {"loan_id": ["l2", "l1", "l3"], "title": ["Trees", "Clouds", "Trees"], "days": [4, 0, 2]}
    )
    assert_frame_equal(result, expected, check_dtype=False)


def test_extra_columns_duplicate_indices_and_inputs_are_preserved() -> None:
    books, borrowed = catalog(), loans()
    books["shelf"] = [2, 3]
    borrowed["note"] = ["a", "b", "c"]
    borrowed.index = pd.Index([8, 8, 2])
    before_books, before_loans = books.copy(deep=True), borrowed.copy(deep=True)
    result = exercise_call(build_loan_report, books, borrowed)
    assert result.index.tolist() == [0, 1, 2]
    assert result.columns.tolist() == ["loan_id", "title", "days"]
    assert result["title"].tolist() == ["Trees", "Clouds", "Trees"]
    result.loc[0, "title"] = "changed"
    assert_frame_equal(books, before_books)
    assert_frame_equal(borrowed, before_loans)


def test_empty_loans_keep_report_schema() -> None:
    result = exercise_call(build_loan_report, catalog(), loans().iloc[:0])
    assert result.empty
    assert result.columns.tolist() == ["loan_id", "title", "days"]


@pytest.mark.parametrize(
    "problem",
    [
        "duplicate_book",
        "null_book",
        "duplicate_loan",
        "null_loan",
        "null_reference",
        "unknown_reference",
    ],
)
def test_bad_keys_fail_instead_of_expanding_or_dropping_rows(problem: str) -> None:
    books, borrowed = catalog(), loans()
    if problem == "duplicate_book":
        books.loc[1, "book_id"] = "b2"
    elif problem == "null_book":
        books.loc[1, "book_id"] = None
    elif problem == "duplicate_loan":
        borrowed.loc[1, "loan_id"] = "l2"
    elif problem == "null_loan":
        borrowed.loc[1, "loan_id"] = None
    elif problem == "null_reference":
        borrowed.loc[1, "book_id"] = None
    else:
        borrowed.loc[1, "book_id"] = "missing"
    with pytest.raises(ValueError, match="key"):
        exercise_call(build_loan_report, books, borrowed)


@pytest.mark.parametrize("values", [[-1, 1.5], [True, "2"], [None, float("nan"), float("inf")]])
def test_invalid_days(values: list[object]) -> None:
    for days in values:
        borrowed = loans()
        borrowed["days"] = pd.Series([days, 0, 2], dtype=object)
        with pytest.raises(ValueError, match="days"):
            exercise_call(build_loan_report, catalog(), borrowed)


def test_missing_or_duplicate_columns() -> None:
    with pytest.raises(ValueError, match="column"):
        exercise_call(build_loan_report, catalog().drop(columns="title"), loans())
    books = pd.DataFrame([["b", "Title", "b"]], columns=["book_id", "title", "book_id"])
    with pytest.raises(ValueError, match="column"):
        exercise_call(build_loan_report, books, loans())
    with pytest.raises(ValueError, match="column"):
        exercise_call(build_loan_report, catalog(), loans().drop(columns="days"))
    borrowed = pd.DataFrame([["l", "b", 1, 2]], columns=["loan_id", "book_id", "days", "days"])
    with pytest.raises(ValueError, match="column"):
        exercise_call(build_loan_report, catalog(), borrowed)
