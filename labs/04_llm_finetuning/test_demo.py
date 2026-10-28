"""Hand-calculated LoRA mechanism, not pretrained-model evaluation."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

torch = pytest.importorskip("torch", reason="Install the opt-in training group")


def mechanism() -> ModuleType:
    path = Path(__file__).with_name("demo.py")
    assert path.is_file(), "The worked low-rank mechanism is not implemented"
    return importlib.import_module("labs.04_llm_finetuning.demo")


def test_rank_one_update_matches_hand_calculation() -> None:
    demo = mechanism()
    result = demo.run_step()
    assert result["input"] == [[1.0, 1.0, 1.0]]
    assert result["before"] == [[1.0, 1.0]]
    assert result["loss_before"] == pytest.approx(4.5)
    assert result["grad_a"] == [[0.0, 0.0, 0.0]]
    assert result["grad_b"] == [[-9.0], [0.0]]
    assert result["after"][0] == pytest.approx([3.7, 1.0])
    assert result["loss_after"] == pytest.approx(0.045, abs=1e-6)
    assert result["trainable_parameters"] == 5
    assert result["frozen_parameters"] == 6
    assert result["base_unchanged"] is True
    assert result["evidence_kind"] == "teacher-algebra-only"


def test_adapter_checkpoint_needs_and_restores_exact_base(tmp_path: Path) -> None:
    demo = mechanism()
    output = tmp_path / "new-run"
    report = demo.run_checkpoint(output)
    assert report["reload_parity"] is True
    assert report["wrong_base_parity"] is False
    assert (output / "base.pt").is_file()
    assert (output / "adapter.pt").is_file()
    assert (output / "mechanism.json").is_file()
    before = (output / "adapter.pt").read_bytes()
    with pytest.raises(FileExistsError):
        demo.run_checkpoint(output)
    assert (output / "adapter.pt").read_bytes() == before


def test_base_receives_no_gradient_and_both_zero_factors_cannot_start() -> None:
    demo = mechanism()
    layer = demo.WorkedRankOne()
    with torch.no_grad():
        layer.a.zero_()
        layer.b.zero_()
    loss = torch.nn.functional.mse_loss(layer(torch.ones(1, 3)), torch.tensor([[4.0, 1.0]]))
    loss.backward()
    assert layer.base.grad is None
    assert torch.equal(layer.a.grad, torch.zeros(1, 3))
    assert torch.equal(layer.b.grad, torch.zeros(2, 1))
