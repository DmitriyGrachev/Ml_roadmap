"""Catalog gate: missing independent live evidence cannot earn strict completion."""

import os
from pathlib import Path

import pytest

from .evidence import validate_submission


def test_independent_live_pooling_comparison() -> None:
    submission = os.environ.get("ROADMAP_RAG_SUBMISSION")
    if not submission:
        pytest.xfail("Independent live learner evidence missing; set ROADMAP_RAG_SUBMISSION")
    validate_submission(Path(submission))
