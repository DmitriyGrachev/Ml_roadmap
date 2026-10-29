"""Preflight and CPU postconditions: no model loads, CUDA or training."""

from argparse import Namespace
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

qlora = import_module("labs.04_llm_finetuning.sft_workflow.qlora")


def test_cuda_required_before_model_loading(tmp_path: Path) -> None:
    data = tmp_path / "data.json"
    data.write_text("[]", encoding="utf-8")
    args = Namespace(
        base=tmp_path,
        tokenizer=tmp_path,
        data=data,
        output=tmp_path / "new",
        max_steps=2,
        max_length=128,
    )
    with pytest.raises(RuntimeError, match="NOT_RUN"):
        qlora.preflight(args, SimpleNamespace(is_available=lambda: False))
    args.max_steps = 100
    with pytest.raises(ValueError, match="limits"):
        qlora.preflight(args, SimpleNamespace())


def test_training_data_uses_explicit_utf8(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import json
    from typing import Any

    expected = [
        {
            "messages": [
                {"role": "user", "content": "маршрут возврата"},
                {"role": "assistant", "content": "返金"},
            ]
        }
    ]
    data = tmp_path / "conversations.json"
    data.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    original = Path.read_text

    def require_utf8(path: Path, *args: Any, **kwargs: Any) -> str:
        assert kwargs.get("encoding") == "utf-8"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", require_utf8)
    assert qlora.read_training_rows(data) == expected


@pytest.mark.parametrize("loss", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_loss_never_writes_status(tmp_path: Path, loss: float) -> None:
    with pytest.raises(ValueError, match="finite training loss"):
        qlora._write_status(tmp_path, loss, device="CPU_FIXTURE", steps=1, max_length=8)
    assert not (tmp_path / "status.json").exists()


@pytest.mark.parametrize("problem", ["missing", "empty", "zero_elements", "nan", "inf"])
def test_invalid_saved_adapter_never_writes_status(tmp_path: Path, problem: str) -> None:
    torch = pytest.importorskip("torch")
    safetensors = pytest.importorskip("safetensors.torch")
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    tensors = {"lora_A.weight": torch.ones((2, 2))}
    if problem == "empty":
        tensors = {}
    elif problem == "zero_elements":
        tensors = {"lora_A.weight": torch.empty((0, 2))}
    elif problem in {"nan", "inf"}:
        tensors["lora_A.weight"][0, 0] = float(problem)
    if problem != "missing":
        safetensors.save_file(tensors, str(adapter / "adapter_model.safetensors"))
    with pytest.raises(ValueError, match="nonempty finite saved adapter"):
        qlora._write_status(tmp_path, 0.5, device="CPU_FIXTURE", steps=1, max_length=8)
    assert not (tmp_path / "status.json").exists()


def test_finite_saved_adapter_retains_loss_in_status(tmp_path: Path) -> None:
    import json

    torch = pytest.importorskip("torch")
    safetensors = pytest.importorskip("safetensors.torch")
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    safetensors.save_file(
        {"lora_A.weight": torch.ones((2, 2))}, str(adapter / "adapter_model.safetensors")
    )
    qlora._write_status(tmp_path, 0.5, device="CPU_FIXTURE", steps=1, max_length=8)
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status["training_loss"] == 0.5
    assert status["status"] == "CUDA_RECIPE_EXECUTED_REQUIRES_REVIEW"
    assert status["learner_credit"] is False
