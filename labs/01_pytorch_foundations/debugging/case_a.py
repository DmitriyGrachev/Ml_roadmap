"""Исходный вариант A. Сохраните для сравнения."""

import torch
from torch import nn
from torch.optim import Optimizer

CONFIG = {"lr": 0.01, "steps": 8}


def step(
    model: nn.Module, optimizer: Optimizer, x: torch.Tensor, y: torch.Tensor, mask: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    model.train()
    prediction = model(x)
    loss = (prediction[mask] - y[mask]).square().mean()
    loss.backward()
    optimizer.zero_grad(set_to_none=True)
    optimizer.step()
    return prediction, loss


def validate(model: nn.Module, x: torch.Tensor) -> torch.Tensor:
    model.eval()
    with torch.no_grad():
        return model(x)  # type: ignore[no-any-return]
