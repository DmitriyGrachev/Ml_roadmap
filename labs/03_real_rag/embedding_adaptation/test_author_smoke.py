"""Opt-in true CPU contrastive backward/update/checkpoint API smoke."""

import os
from importlib import import_module
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_RANKING") != "1",
    reason="Use ranking group and ROADMAP_RUN_RANKING=1",
)


def test_actual_triplet_loss_gradients_update_and_save_reload(tmp_path: Path) -> None:
    author = import_module("labs.03_real_rag.embedding_adaptation.author")
    result = author.smoke(tmp_path / "random-adaptation")
    assert result["evidence_kind"] == "AUTHOR_RANDOM_API_SMOKE"
    assert result["gradient_norm"] > 0
    assert result["parameter_change"] > 0
    assert result["reload_max_error"] < 1e-6
    assert result["steps"] == 2
