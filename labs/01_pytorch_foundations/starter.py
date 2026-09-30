"""Student-owned PyTorch exercise boundaries; see README for the Russian contract."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import torch
    from torch import nn
    from torch.optim import Optimizer
    from torch.utils.data import DataLoader


class EpochMetrics(TypedDict):
    count: int
    loss: float


class ValidationMetrics(EpochMetrics):
    accuracy: float


class PredictionError(TypedDict):
    id: str
    actual: int
    predicted: int


def make_loaders(
    features: Sequence[Sequence[float]],
    labels: Sequence[int],
    *,
    train_indices: Sequence[int],
    validation_indices: Sequence[int],
    batch_size: int,
    seed: int,
) -> tuple[
    DataLoader[tuple[torch.Tensor, torch.Tensor]], DataLoader[tuple[torch.Tensor, torch.Tensor]]
]:
    """Create isolated, reproducible train/validation loaders without dropping rows."""
    raise NotImplementedError("Build a Dataset and deterministic DataLoaders")


def build_model(*, input_dim: int, n_classes: int) -> nn.Module:
    """Return a trainable Module mapping [batch, input_dim] to class logits."""
    raise NotImplementedError("Define a Module with forward logits")


def prepare_batch(
    batch: tuple[torch.Tensor, torch.Tensor], device: torch.device
) -> tuple[torch.Tensor, torch.Tensor]:
    """Validate shape/finite values and transfer float32 features/int64 labels."""
    raise NotImplementedError("Check a batch before transfer to the selected device")


def train_epoch(
    model: nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    optimizer: Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> EpochMetrics:
    """Train one epoch; return row-weighted mean loss and row count."""
    raise NotImplementedError("Implement zero_grad, forward, loss, backward and step")


def validate_epoch(
    model: nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    criterion: nn.Module,
    device: torch.device,
) -> ValidationMetrics:
    """Evaluate without gradients or weight updates; report loss and accuracy."""
    raise NotImplementedError("Implement eval-mode validation on every row")


def analyze_errors(
    logits: torch.Tensor, labels: torch.Tensor, ids: Sequence[str]
) -> list[PredictionError]:
    """Return every mistake in input order; argmax ties choose the first class."""
    raise NotImplementedError("Inspect wrong predictions using stable object IDs")


def save_checkpoint(
    path: Path, model: nn.Module, optimizer: Optimizer, metadata: dict[str, object]
) -> None:
    """Save model_state, optimizer_state and primitive metadata, never the model object."""
    raise NotImplementedError("Save a state-dict-only checkpoint")


def load_checkpoint(
    path: Path, model: nn.Module, optimizer: Optimizer, device: torch.device
) -> dict[str, object]:
    """Restore weights/optimizer with weights_only=True and a device map."""
    raise NotImplementedError("Safely reload the checkpoint and return metadata")


def predict_classes(model: nn.Module, features: torch.Tensor, device: torch.device) -> list[int]:
    """Return one integer class for each feature row under eval/no_grad."""
    raise NotImplementedError("Run inference on new object features")
