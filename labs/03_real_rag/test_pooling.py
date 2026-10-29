"""Masked pooling preserves valid-token geometry and explicit CLS compatibility."""

from importlib import import_module
from pathlib import Path

import numpy as np
import pytest

dense = import_module("labs.03_real_rag.dense")


def test_masked_mean_ignores_padding_and_normalizes() -> None:
    hidden = np.array([[[3.0, 0.0], [0.0, 4.0], [900.0, -900.0]]])
    result = dense.masked_mean_pooling(hidden, [[1, 1, 0]])
    np.testing.assert_allclose(result, [[0.6, 0.8]])
    np.testing.assert_allclose(dense.masked_mean_pooling(hidden[:, :2], [[1, 1]]), result)


@pytest.mark.parametrize(
    ("hidden", "mask"),
    [
        ([[[1.0, 0.0]]], [[0]]),
        ([[[0.0, 0.0]]], [[1]]),
        ([[[float("nan"), 0.0]]], [[1]]),
        ([[[1.0, 0.0]]], [[2]]),
        ([[[1.0, 0.0]]], [[1, 1]]),
        ([[1.0, 0.0]], [[1]]),
        ([[[1.0, 0.0]]], [[0.5]]),
        ([[[True, False]]], [[1]]),
    ],
)
def test_invalid_mask_or_hidden_fails_closed(hidden: object, mask: object) -> None:
    with pytest.raises(ValueError, match=r"pooling|vectors"):
        dense.masked_mean_pooling(hidden, mask)


def test_explicit_pooling_identity_preserves_old_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        dense,
        "verified_minilm_identity",
        lambda _: {
            "pooling": "first-token-last-hidden-state-l2-v1",
            "evidence": "EXPERIMENTAL_CLS_BASELINE_NOT_MODEL_CARD_MEAN_POOLING",
        },
    )
    # Invalid mode rejected before optional loaders are imported.
    with pytest.raises(ValueError, match="pooling"):
        dense.encode_local_minilm(tmp_path, ("text",), pooling="max")


def test_actual_optional_encoder_uses_masked_mean_and_preserves_cls_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    torch = pytest.importorskip("torch", reason="Optional local CPU encoder mechanics")
    transformers = pytest.importorskip(
        "transformers", reason="Optional local CPU encoder mechanics"
    )
    torch.manual_seed(7)
    torch.set_num_threads(1)
    tokenizer = transformers.BertTokenizer(
        vocab={
            "[PAD]": 0,
            "[UNK]": 1,
            "[CLS]": 2,
            "[SEP]": 3,
            "[MASK]": 4,
            "red": 5,
            "blue": 6,
            "square": 7,
        }
    )
    tokenizer.save_pretrained(tmp_path)
    model = transformers.BertModel(
        transformers.BertConfig(
            vocab_size=8,
            hidden_size=384,
            num_hidden_layers=1,
            num_attention_heads=6,
            intermediate_size=32,
            hidden_dropout_prob=0.0,
            attention_probs_dropout_prob=0.0,
        )
    )
    model.save_pretrained(tmp_path)
    monkeypatch.setattr(
        dense,
        "verified_minilm_identity",
        lambda _: {
            "pooling": "first-token-last-hidden-state-l2-v1",
            "evidence": "EXPERIMENTAL_CLS_BASELINE_NOT_MODEL_CARD_MEAN_POOLING",
        },
    )
    cls, cls_identity = dense.encode_local_minilm(tmp_path, ("red", "red blue square"))
    mean, mean_identity = dense.encode_local_minilm(
        tmp_path, ("red", "red blue square"), pooling="masked_mean"
    )
    alone, _ = dense.encode_local_minilm(tmp_path, ("red",), pooling="masked_mean")
    assert cls_identity["pooling"] == "first-token-last-hidden-state-l2-v1"
    assert mean_identity["pooling"] == "attention-mask-mean-last-hidden-state-l2-v1"
    assert not np.allclose(cls, mean)
    np.testing.assert_allclose(mean[:1], alone, atol=1e-6)
