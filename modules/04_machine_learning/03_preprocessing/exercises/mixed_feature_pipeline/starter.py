"""Build an unfitted pipeline; learn all preprocessing state during fit."""

from sklearn.pipeline import Pipeline


def build_visit_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    """Return the named mixed-feature Ridge pipeline described in the README.

    Validate feature declarations, preserve the caller's lists, and create fresh
    unfitted components on each call. Training data is deliberately not an argument.
    """
    raise NotImplementedError("Implement the mixed-feature park-visit pipeline")
