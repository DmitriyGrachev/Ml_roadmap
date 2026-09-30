"""Учебные границы: реализуйте самостоятельно, сохраняя контракты README."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from torch import Tensor

LABELS = ("create_account", "delete_account", "edit_account", "switch_account")


@dataclass(frozen=True)
class Document:
    row_id: str
    text: str
    label: int


@dataclass(frozen=True)
class RunConfig:
    seed: int = 17
    batch_size: int = 4
    max_length: int = 64
    max_steps: int = 20
    learning_rate: float = 2e-5


@dataclass(frozen=True)
class TrainingHistory:
    steps: int
    train_losses: tuple[float, ...]
    validation_loss: float
    validation_count: int


def prepare_splits(
    rows: Sequence[Mapping[str, str]],
    *,
    seed: int,
    counts: tuple[int, int, int] = (64, 16, 16),
) -> dict[str, list[Document]]:
    """Filter four intents, reject conflicting duplicates, then split stable content IDs."""
    raise NotImplementedError("Подготовьте воспроизводимые train/validation/test после dedup")


def encode_batch(tokenizer: Any, texts: Sequence[str], *, max_length: int) -> dict[str, Tensor]:
    """Validate nonempty texts; return padded/truncated integer BERT inputs on CPU."""
    raise NotImplementedError("Токенизируйте батч и проверьте attention_mask")


def masked_mean_pool(hidden: Tensor, attention_mask: Tensor) -> Tensor:
    """Exclude padding from the mean, then L2-normalize each sentence vector."""
    raise NotImplementedError("Реализуйте masked mean pooling и нормализацию")


def adapt_encoder(
    model: Any,
    tokenizer: Any,
    training: Sequence[Document],
    validation: Sequence[Document],
    config: RunConfig,
) -> TrainingHistory:
    """Train only last BERT block + classifier; evaluate all validation rows once frozen."""
    raise NotImplementedError("Настройте trainable параметры и ограниченный training loop")


def save_and_reload(model: Any, tokenizer: Any, directory: Path) -> tuple[Any, Any]:
    """Save safetensors/tokenizer and reload locally in eval mode, with no remote code."""
    raise NotImplementedError("Сохраните classifier/tokenizer и загрузите их локально")


def compare_models(
    model_directory: Path,
    splits: Mapping[str, Sequence[Document]],
    config: RunConfig,
    output_directory: Path,
) -> dict[str, dict[str, object]]:
    """Measure TF-IDF/linear, frozen embeddings/linear and adapted encoder on same test IDs.

    Return per-method predictions, accuracy, macro_f1, warm_seconds,
    peak_memory_bytes and memory_note. Save the adapted checkpoint in output_directory.
    The first two classifiers use LogisticRegression(max_iter=300, random_state=seed).
    See README: no test-driven selection and no universal accuracy threshold.
    """
    raise NotImplementedError("Проведите три сопоставимых эксперимента и сохраните результаты")


def run_offline_experiment(output_directory: Path, config: RunConfig) -> None:
    """Exercise your boundaries on local_fixture.rows(); save report and learner analysis.

    Use make_local_components(num_labels=4), prepare_splits(counts=(2, 1, 1)),
    adapt_encoder and save_and_reload. This is offline completion evidence only.
    Required files and their schema are documented in README.
    """
    raise NotImplementedError("Соберите собственный offline experiment и объясните результат")
