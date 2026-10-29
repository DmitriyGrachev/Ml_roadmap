"""The author demonstrates one fixed split, never learner model selection."""

from .example import run_example


def test_fixed_pipeline_fits_train_only_and_handles_unseen_categories() -> None:
    result = run_example()
    assert result["train_rows"] == 8
    assert result["heldout_rows"] == 2
    assert result["training_median"] == 0.0
    assert result["categories"] == ["east", "west"]
    assert result["predictions"] == [0, 1]
