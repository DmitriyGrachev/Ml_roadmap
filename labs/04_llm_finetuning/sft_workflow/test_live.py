"""Strict target: absence of independently submitted evidence is an unfinished learner task."""

import os
from importlib import import_module
from pathlib import Path

from roadmap_tools.exercise import exercise_call


def submitted_evidence() -> Path:
    location = os.environ.get("ROADMAP_SFT_EVIDENCE")
    if not location:
        raise NotImplementedError("Submit independent live evidence via ROADMAP_SFT_EVIDENCE")
    return Path(location)


def test_independent_pretrained_evidence() -> None:
    evidence = import_module("labs.04_llm_finetuning.sft_workflow.evidence")
    root = exercise_call(submitted_evidence)
    assert evidence.validate_evidence(root) == "REQUIRES_REVIEW"
