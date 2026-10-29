"""Opt-in actual CrossEncoder predict/rank; random weights imply no retrieval quality."""

import math
import os
from importlib import import_module
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_RANKING") != "1",
    reason="Explicit ranking group and ROADMAP_RUN_RANKING=1 required",
)


def test_actual_cross_encoder_predict_and_rank(tmp_path: Path) -> None:
    author = import_module("labs.03_real_rag.neural_reranking.author")
    model = author.tiny_model(tmp_path / "random-cross-encoder")
    pairs = [("printer paper", "printer paper"), ("printer paper", "scan settings")]
    scores = model.predict(pairs, batch_size=2, show_progress_bar=False)
    ranked = model.rank(
        "printer paper", [p[1] for p in pairs], return_documents=True, show_progress_bar=False
    )
    assert scores.shape == (2,)
    assert all(math.isfinite(float(v)) for v in scores)
    assert [r["corpus_id"] for r in ranked] == sorted(range(2), key=lambda i: -scores[i])
    assert [float(r["score"]) for r in ranked] == pytest.approx(sorted(scores, reverse=True))
    assert all(r["text"] == pairs[r["corpus_id"]][1] for r in ranked)
