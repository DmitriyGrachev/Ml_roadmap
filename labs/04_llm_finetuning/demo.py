"""One hand-calculable low-rank update, not PEFT or a language-model experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch import nn


class WorkedRankOne(nn.Module):
    """Fixed 3 -> 2 teacher map with rank one and scale one, no bias/dropout."""

    def __init__(self) -> None:
        super().__init__()
        self.base = nn.Parameter(
            torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]), requires_grad=False
        )
        self.a = nn.Parameter(torch.tensor([[1.0, 1.0, 1.0]]))
        self.b = nn.Parameter(torch.zeros(2, 1))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return inputs @ self.base.T + (inputs @ self.a.T) @ self.b.T


def _step() -> tuple[WorkedRankOne, dict[str, object]]:
    model = WorkedRankOne()
    inputs = torch.tensor([[1.0, 1.0, 1.0]])
    target = torch.tensor([[4.0, 1.0]])
    original = model.base.detach().clone()
    optimizer = torch.optim.SGD([model.a, model.b], lr=0.1)
    before = model(inputs)
    loss = nn.functional.mse_loss(before, target)
    optimizer.zero_grad()
    torch.autograd.backward(loss)
    assert model.a.grad is not None
    assert model.b.grad is not None
    grad_a = model.a.grad.detach().tolist()
    grad_b = model.b.grad.detach().tolist()
    optimizer.step()
    with torch.inference_mode():
        after = model(inputs)
        loss_after = nn.functional.mse_loss(after, target)
    report: dict[str, object] = {
        "evidence_kind": "teacher-algebra-only",
        "device": "cpu",
        "dtype": "float32",
        "torch_version": torch.__version__,
        "seed": None,
        "seed_reason": "All tensors are explicit constants; no random initialization",
        "rank": 1,
        "scale": 1,
        "learning_rate": 0.1,
        "input": inputs.tolist(),
        "target": target.tolist(),
        "before": before.detach().tolist(),
        "after": after.tolist(),
        "loss_before": float(loss.detach()),
        "loss_after": float(loss_after),
        "grad_a": grad_a,
        "grad_b": grad_b,
        "trainable_parameters": model.a.numel() + model.b.numel(),
        "frozen_parameters": model.base.numel(),
        "base_unchanged": torch.equal(original, model.base.detach()),
    }
    return model, report


def run_step() -> dict[str, object]:
    """Return observed numbers for the fixed teaching example."""
    return _step()[1]


def run_checkpoint(output: Path) -> dict[str, object]:
    """Save our own constants and adapter separately, reload, then show a wrong base."""
    output.mkdir(parents=True, exist_ok=False)
    model, report = _step()
    torch.save({"base": model.base.detach()}, output / "base.pt")
    torch.save({"a": model.a.detach(), "b": model.b.detach()}, output / "adapter.pt")
    # Only files this invocation just wrote are loaded. This is not an arbitrary loader.
    base = torch.load(output / "base.pt", map_location="cpu", weights_only=True)
    adapter = torch.load(output / "adapter.pt", map_location="cpu", weights_only=True)
    restored = WorkedRankOne()
    restored.load_state_dict({**base, **adapter})
    inputs = torch.tensor([[1.0, 1.0, 1.0]])
    with torch.inference_mode():
        expected = model(inputs)
        report["reload_parity"] = torch.equal(expected, restored(inputs))
        restored.base.add_(1.0)
        report["wrong_base_parity"] = torch.equal(expected, restored(inputs))
    (output / "mechanism.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional NEW directory for own-file reload")
    args = parser.parse_args()
    result = run_step() if args.output is None else run_checkpoint(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
