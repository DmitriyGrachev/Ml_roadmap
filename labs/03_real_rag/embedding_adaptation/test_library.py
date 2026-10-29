"""Learner fit must change actual model parameters and roundtrip a checkpoint."""

import os
from importlib import import_module
from pathlib import Path

import pytest

from roadmap_tools import exercise_call

pytestmark = pytest.mark.skipif(
    os.environ.get("ROADMAP_RUN_RANKING") != "1",
    reason="Use ranking group and ROADMAP_RUN_RANKING=1",
)


def test_learner_contrastive_fit_changes_actual_model(tmp_path: Path) -> None:
    torch = import_module("torch")
    st = import_module("sentence_transformers")
    author = import_module("labs.03_real_rag.embedding_adaptation.author")
    starter = import_module("labs.03_real_rag.embedding_adaptation.starter")
    model = author.tiny_model(tmp_path / "initial")
    before = [p.detach().clone() for p in model.parameters()]
    triples = [
        {
            "query_id": "q",
            "query": "printer paper",
            "positive_id": "p",
            "positive": "paper printer",
            "negative_id": "n",
            "negative": "scan settings",
            "family": "printer",
            "split": "train",
        }
    ]
    trained = exercise_call(starter.fit_encoder, model, triples, steps=2, seed=7)
    assert trained is model
    assert any(
        not torch.equal(old, new) for old, new in zip(before, model.parameters(), strict=True)
    )
    assert any(
        p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0
        for p in model.parameters()
    )
    checkpoint = tmp_path / "adapted"
    model.save_pretrained(str(checkpoint))
    loaded = st.SentenceTransformer(
        str(checkpoint), local_files_only=True, device="cpu", trust_remote_code=False
    )
    expected = model.encode(
        ["printer paper"],
        normalize_embeddings=True,
        convert_to_tensor=True,
        show_progress_bar=False,
    )
    actual = loaded.encode(
        ["printer paper"],
        normalize_embeddings=True,
        convert_to_tensor=True,
        show_progress_bar=False,
    )
    torch.testing.assert_close(actual, expected, atol=1e-6, rtol=1e-6)
