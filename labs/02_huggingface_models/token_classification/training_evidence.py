"""Test-only observation of the supplied model; contains no learner training loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OptimizationEvidence:
    before: dict[str, Any]
    losses: list[float] = field(default_factory=list)
    loss_backward: list[bool] = field(default_factory=list)
    gradients: list[tuple[bool, bool]] = field(default_factory=list)
    labels: list[Any] = field(default_factory=list)
    input_ids: list[Any] = field(default_factory=list)
    collation_calls: int = 0


def observe_optimization(model: Any, monkeypatch: Any) -> OptimizationEvidence:
    from importlib import import_module

    torch = import_module("torch")
    transformers = import_module("transformers")
    evidence = OptimizationEvidence({n: p.detach().clone() for n, p in model.named_parameters()})
    real_collate = transformers.DataCollatorForTokenClassification.__call__

    def collate(current: Any, *args: Any, **kwargs: Any) -> Any:
        evidence.collation_calls += 1
        return real_collate(current, *args, **kwargs)

    monkeypatch.setattr(transformers.DataCollatorForTokenClassification, "__call__", collate)

    def observe(current: Any, args: Any, kwargs: Any, output: Any) -> None:
        if model.training and "labels" in kwargs:
            labels = kwargs["labels"]
            evidence.labels.append(labels.detach().clone())
            evidence.input_ids.append(kwargs["input_ids"].detach().clone())
            assert bool((labels != -100).any()), (
                "all-ignored batch must be skipped before model loss"
            )
            assert bool(torch.isfinite(output.loss)), "active-label loss must be finite"
            evidence.losses.append(float(output.loss.detach()))
            output.loss.register_hook(
                lambda grad: evidence.loss_backward.append(bool(torch.isfinite(grad).all()))
            )

    model.register_forward_hook(observe, with_kwargs=True)
    for parameter in model.parameters():
        if parameter.requires_grad:
            parameter.register_hook(
                lambda grad: evidence.gradients.append(
                    (bool(torch.isfinite(grad).all()), bool((grad != 0).any()))
                )
            )
    return evidence


def require_optimization(evidence: OptimizationEvidence, model: Any) -> None:
    from importlib import import_module

    torch = import_module("torch")
    assert evidence.loss_backward, "finite loss backward required"
    assert all(evidence.loss_backward), "finite loss backward required"
    assert evidence.losses, "finite active-label loss required"
    assert evidence.gradients
    assert all(finite for finite, _ in evidence.gradients)
    assert any(nonzero for _, nonzero in evidence.gradients), "nonzero trainable gradient required"
    assert any(
        not torch.equal(evidence.before[name], value.detach())
        for name, value in model.named_parameters()
    ), "optimizer must change model parameters"
    assert evidence.collation_calls, "actual DataCollatorForTokenClassification required"
