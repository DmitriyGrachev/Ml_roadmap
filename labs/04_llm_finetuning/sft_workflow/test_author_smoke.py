"""Teacher-only optional API regression; excluded from catalog completion targets."""

import os
from importlib import import_module
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_SFT") != "1", reason="Explicit ROADMAP_RUN_SFT=1 required"
)


def test_bounded_author_trl_peft_mechanism(tmp_path: Path) -> None:
    module = import_module("labs.04_llm_finetuning.sft_workflow.author_smoke")
    result = module.run(tmp_path / "author", steps=2)
    assert result["evidence_kind"] == "RANDOM_MECHANISM_ONLY"
    assert result["review_status"] == "NO_LEARNER_CREDIT"
    assert result["base_unchanged"]
    assert result["adapter_changed_count"] > 0
    assert result["reload_equal"]
    assert result["causal_mask_loss_equal"]
