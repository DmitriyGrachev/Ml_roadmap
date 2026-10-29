"""Independent live learner evidence is mandatory for strict completion."""

import os
from importlib import import_module
from pathlib import Path

import pytest


def test_independent_local_pretrained_submission() -> None:
    submission = os.environ.get("ROADMAP_RERANKING_SUBMISSION")
    if not submission:
        pytest.xfail(
            "Provide independently reviewed live evidence via ROADMAP_RERANKING_SUBMISSION"
        )
    import_module("labs.03_real_rag.neural_reranking.runtime").validate_submission(Path(submission))
