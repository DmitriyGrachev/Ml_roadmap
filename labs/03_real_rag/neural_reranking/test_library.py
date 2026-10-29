"""Real local library learner contract; no author fallback for rerank/metrics."""

import os
from importlib import import_module
from pathlib import Path

import pytest

from roadmap_tools import exercise_call

pytestmark = pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_RANKING") != "1",
    reason="Use ranking group and ROADMAP_RUN_RANKING=1",
)


def test_learner_uses_actual_cross_encoder_scores(tmp_path: Path) -> None:
    author = import_module("labs.03_real_rag.neural_reranking.author")
    starter = import_module("labs.03_real_rag.neural_reranking.starter")
    model = author.tiny_model(tmp_path / "random-cross-encoder")
    candidates = [{"id": "b", "text": "printer paper"}, {"id": "a", "text": "scan settings"}]
    expected = model.predict([("paper", c["text"]) for c in candidates], show_progress_bar=False)
    result = exercise_call(
        starter.rerank,
        "paper",
        candidates,
        lambda pairs: model.predict(pairs, show_progress_bar=False).tolist(),
        2,
    )
    scores = {c["id"]: float(score) for c, score in zip(candidates, expected, strict=True)}
    assert [r["id"] for r in result] == sorted(scores, key=lambda i: (-scores[i], i))
    assert [r["score"] for r in result] == pytest.approx([scores[r["id"]] for r in result])
