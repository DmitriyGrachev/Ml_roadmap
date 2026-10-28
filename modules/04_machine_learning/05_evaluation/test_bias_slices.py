"""Literal counts detect reversed cells, wrong denominators and lost empty groups."""

# Error message wording is outside this boundary.
# ruff: noqa: PT011
from importlib import import_module

import pytest

bias = import_module("modules.04_machine_learning.05_evaluation.bias_slices")


def test_counts_and_conditioning_denominators() -> None:
    rows = (("A", 1, 1), ("A", 1, 0), ("A", 0, 1), ("A", 0, 0), ("A", 0, 0))
    result = bias.summarize_rows(rows, groups=("B", "A"))
    assert list(result) == ["B", "A"]
    assert result["A"] == {
        "support": 5,
        "positives": 2,
        "negatives": 3,
        "predicted_positives": 2,
        "tp": 1,
        "fp": 1,
        "fn": 1,
        "tn": 2,
        "selection_rate": 0.4,
        "tpr": 0.5,
        "fpr": 1 / 3,
        "precision": 0.5,
        "accuracy": 0.6,
    }


def test_empty_group_retains_counts_and_undefined_rates() -> None:
    result = bias.summarize_rows((), groups=("absent",))["absent"]
    assert result == {
        "support": 0,
        "positives": 0,
        "negatives": 0,
        "predicted_positives": 0,
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "tn": 0,
        "selection_rate": None,
        "tpr": None,
        "fpr": None,
        "precision": None,
        "accuracy": None,
    }


def test_no_positive_labels_is_distinct_from_zero_true_positive_rate() -> None:
    result = bias.summarize_rows((("A", 0, 0),), groups=("A",))["A"]
    assert result["tpr"] is None
    assert result["precision"] is None
    assert result["fpr"] == result["selection_rate"] == 0.0
    positive = bias.summarize_rows((("A", 1, 0),), groups=("A",))["A"]
    assert positive["tpr"] == 0.0
    assert positive["fpr"] is None
    assert positive["precision"] is None


@pytest.mark.parametrize("groups", [(), ("A", "A"), (" ",)])
def test_invalid_group_declaration(groups: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        bias.summarize_rows((), groups=groups)


@pytest.mark.parametrize(
    "rows",
    [
        (("B", 0, 0),),
        (("A", 2, 0),),
        (("A", 0, -1),),
        (("A", True, 0),),
        (("A", 0, 1.0),),
        (("A", "1", 0),),
    ],
)
def test_wrong_groups_and_nonbinary_labels_rejected(rows: tuple[tuple[object, ...], ...]) -> None:
    with pytest.raises(ValueError):
        bias.summarize_rows(rows, groups=("A",))


def test_inputs_unchanged_and_outputs_independent() -> None:
    rows, groups = (("A", 1, 0),), ("A", "B")
    first = bias.summarize_rows(rows, groups=groups)
    first["A"]["tp"] = 999
    assert bias.summarize_rows(rows, groups=groups)["A"]["tp"] == 0
    assert rows == (("A", 1, 0),)
    assert groups == ("A", "B")


def test_sampling_demo_changes_composition_without_changing_slice_rates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    before, after = bias.sampling_demo()
    assert [before[g]["support"] for g in ("A", "B", "all")] == [8, 4, 12]
    assert [after[g]["support"] for g in ("A", "B", "all")] == [8, 12, 20]
    assert before["all"]["accuracy"] == pytest.approx(2 / 3)
    assert after["all"]["accuracy"] == 0.6
    assert before["A"]["tpr"] == after["A"]["tpr"] == 0.75
    assert before["B"]["fpr"] == after["B"]["fpr"] == 0.5
    bias.main()
    first = capsys.readouterr().out
    bias.main()
    assert capsys.readouterr().out == first
    assert "before all 12 4 2 2 4 0.667 0.333 0.667" in first
    assert "after all 20 6 4 4 6 0.600 0.400 0.600" in first
