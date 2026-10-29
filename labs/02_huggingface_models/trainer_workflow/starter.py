"""Learner boundaries. No completed author orchestration is called here."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .protocol import RunConfig


def tokenize_dataset(dataset: Any, tokenizer: Any, max_length: int) -> Any:
    """Batched Dataset.map, truncate, no padding; retain only model inputs + labels."""
    raise NotImplementedError("Implement batched map and remove non-input columns")


def build_collator(tokenizer: Any) -> Any:
    """Return the actual DataCollatorWithPadding(padding=True, return_tensors='pt')."""
    raise NotImplementedError("Implement dynamic padding")


def make_training_arguments(output: Path, config: RunConfig) -> Any:
    """CPU; eval/save each step, best accuracy, no reporters; retain <=2 checkpoints.

    Preserve optimizer state for resume, plus selected final export.
    """
    raise NotImplementedError("Configure TrainingArguments")


def compute_metrics(evaluation: Any) -> dict[str, float]:
    """Argmax [N,C] logits; return accuracy; reject malformed/nonfinite arrays."""
    raise NotImplementedError("Implement validation metrics")


def train_model(
    model: Any,
    tokenizer: Any,
    splits: Any,
    output: Path,
    config: RunConfig,
    resume_from_checkpoint: Path | None = None,
) -> dict[str, Any]:
    """Validate split IDs/config; use the four boundaries above and actual Trainer.

    Save best model + tokenizer to output/final, reload locally and predict test
    once. Return history, best_metric, best_checkpoint, global_step, predictions,
    references, split_ids, model_identity, reload_identity, tokenizer_identity, checkpoint_path.
    history contains raw eval log rows, not invented/interpolated values.
    """
    raise NotImplementedError("Implement Trainer orchestration and checkpoint resume")
