"""Learner alignment, entity metrics and actual local-model training boundaries."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any


def align_labels(word_ids: Sequence[int | None], word_labels: Sequence[int]) -> list[int]:
    """First subword gets word label; special/continuation gets -100.

    Word IDs start at 0, are nondecreasing and cannot skip an unseen word.
    A word cannot resume after None (or another word); windows starting in a
    continuation must be rejected upstream. Empty/all-special input is legal.
    """
    raise NotImplementedError("Implement first-subword alignment")


def entity_metrics(
    predictions: Sequence[Sequence[str]], references: Sequence[Sequence[str]]
) -> dict[str, float | int]:
    """Exact BIO spans per sentence; reject invalid I on either side.

    Return precision, recall, f1, tp, fp, fn. Zero denominators yield 0.0.
    Matching type with wrong boundary is one FP plus one FN. Do not join rows.
    """
    raise NotImplementedError("Implement exact entity-span metrics")


def train_token_classifier(
    model: Any,
    tokenizer: Any,
    splits: Any,
    output: Path,
    max_steps: int = 2,
    *,
    max_length: int = 32,
    batch_size: int = 2,
) -> dict[str, Any]:
    """Actual AutoModelForTokenClassification; use align_labels/entity_metrics.

    Validate disjoint IDs/BIO/config first. Batched map is_split_into_words=True,
    dynamic DataCollatorForTokenClassification(label_pad_token_id=-100), CPU,
    declared 1..100 optimizer-step budget (author tests <=4). Keep full source
    tags and offsets to audit entities cut
    at truncation; exclude incomplete entities from supported span scoring and
    count them. Never backprop an all-ignored batch (undefined mean loss).
    Save/reload safe local model; return per-row word predictions, references,
    span_metrics, coverage, split_ids, history, checkpoint_path, model_identity,
    reload_identity, tokenizer_identity, optimizer_steps, skipped_all_ignored_batches.
    No active batches means zero optimizer_steps, explicit skipped count and unchanged
    saved model; do not repeat an empty epoch indefinitely. Holdout is read only
    after validation-based model selection.
    """
    raise NotImplementedError("Implement local token-classifier experiment")
