"""Learner completion requires a separate actual local pretrained experiment."""

import os
from importlib import import_module
from pathlib import Path

import pytest


def test_independent_local_pretrained_submission() -> None:
    submission = os.environ.get("ROADMAP_ADAPTATION_SUBMISSION")
    if not submission:
        pytest.xfail(
            "Provide independently reviewed live evidence via ROADMAP_ADAPTATION_SUBMISSION"
        )
    import_module("labs.03_real_rag.embedding_adaptation.runtime").validate_submission(
        Path(submission)
    )
