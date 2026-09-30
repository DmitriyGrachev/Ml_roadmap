"""Learner-owned offline ranking study."""

from pathlib import Path


def run_study(output_dir: Path) -> Path:
    """Compare two selected methods on group-held-out queries and save evidence.

    Refuse an existing directory; call the existing graded and paired metrics.
    Preserve immutable fixtures and report incomplete judgments and access policy.
    """
    # TODO: choose methods, split groups, rank authorized documents, save actual results.
    raise NotImplementedError("Implement the offline ranking study")
