"""Independent acceptance checks for learner-owned TODO boundaries."""

from copy import deepcopy
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from roadmap_tools import exercise_call

torch = pytest.importorskip("torch", reason="Install the optional training group")
from torch import Tensor, nn  # noqa: E402

starter = import_module("labs.01_pytorch_foundations.starter")


class ForwardModeProbe(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.dropout = nn.Dropout(0.5)
        self.linear = nn.Linear(2, 2)
        self.forward_modes: list[tuple[bool, bool]] = []

    def forward(self, features: Tensor) -> Tensor:
        self.forward_modes.append((self.training, torch.is_grad_enabled()))
        logits: Tensor = self.linear(self.dropout(features))
        return logits


def test_loaders_keep_splits_disjoint_and_include_last_uneven_batch() -> None:
    rows = [[float(i), float(i % 3)] for i in range(11)]
    labels = [i % 2 for i in range(11)]
    train, validation = exercise_call(
        starter.make_loaders,
        rows,
        labels,
        train_indices=list(range(8)),
        validation_indices=[8, 9, 10],
        batch_size=3,
        seed=17,
    )
    train_batches = list(train)
    validation_batches = list(validation)
    assert sum(len(y) for _, y in train_batches) == 8
    assert [len(y) for _, y in validation_batches] == [3]
    assert sorted(float(x[0]) for batch, _ in train_batches for x in batch) == list(range(8))
    assert sorted(float(x[0]) for batch, _ in validation_batches for x in batch) == [8, 9, 10]
    assert train_batches[0][0].dtype == torch.float32
    assert train_batches[0][1].dtype == torch.int64


def test_loaders_reject_overlap_and_bad_rows() -> None:
    with pytest.raises(ValueError, match=r"split|overlap"):
        exercise_call(
            starter.make_loaders,
            [[0.0], [1.0]],
            [0, 1],
            train_indices=[0],
            validation_indices=[0],
            batch_size=1,
            seed=1,
        )
    with pytest.raises(ValueError, match=r"finite|feature"):
        exercise_call(
            starter.make_loaders,
            [[float("nan")], [1.0]],
            [0, 1],
            train_indices=[0],
            validation_indices=[1],
            batch_size=1,
            seed=1,
        )


def test_loaders_reject_empty_and_duplicate_split_indices() -> None:
    for train_indices, validation_indices in [([], [1]), ([0, 0], [1])]:
        with pytest.raises(ValueError, match=r"split|index|duplicate|empty"):
            exercise_call(
                starter.make_loaders,
                [[0.0], [1.0]],
                [0, 1],
                train_indices=train_indices,
                validation_indices=validation_indices,
                batch_size=1,
                seed=1,
            )


def test_model_forward_shape_and_autograd() -> None:
    model = exercise_call(starter.build_model, input_dim=4, n_classes=3)
    x = torch.randn(5, 4)
    logits = model(x)
    assert logits.shape == (5, 3)
    assert logits.dtype.is_floating_point
    logits.sum().backward()
    assert any(parameter.grad is not None for parameter in model.parameters())


def test_prepare_batch_preserves_device_shapes_and_rejects_nonfinite() -> None:
    x, y = exercise_call(
        starter.prepare_batch,
        (torch.tensor([[1.0, 2.0]]), torch.tensor([1])),
        torch.device("cpu"),
    )
    assert x.shape == (1, 2)
    assert y.shape == (1,)
    assert x.dtype == torch.float32
    assert y.dtype == torch.int64
    assert x.device.type == y.device.type == "cpu"
    with pytest.raises(ValueError, match="finite"):
        exercise_call(
            starter.prepare_batch,
            (torch.tensor([[float("inf"), 1.0]]), torch.tensor([0])),
            torch.device("cpu"),
        )


def test_train_epoch_updates_weights_and_weights_uneven_batches_by_rows() -> None:
    torch.manual_seed(7)
    model = ForwardModeProbe()
    model.eval()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    criterion = nn.CrossEntropyLoss()
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0], [0.2, 0.8], [0.8, 0.2], [0.4, 0.6]])
    y = torch.tensor([0, 1, 0, 1, 0])
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x, y), batch_size=2)
    before = [p.detach().clone() for p in model.parameters()]
    result = exercise_call(
        starter.train_epoch, model, loader, optimizer, criterion, torch.device("cpu")
    )
    assert result["count"] == 5
    assert result["loss"] >= 0
    assert torch.isfinite(torch.tensor(result["loss"]))
    assert any(not torch.equal(a, b) for a, b in zip(before, model.parameters(), strict=True))
    assert model.training
    assert model.forward_modes == [(True, True)] * 3


def test_train_epoch_reports_row_weighted_loss_for_uneven_batches() -> None:
    model = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.0)
    criterion = nn.CrossEntropyLoss()
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0], [0.2, 0.8]])
    y = torch.tensor([0, 1, 0])
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x, y), batch_size=2)
    expected = criterion(model(x), y).item()
    result = exercise_call(
        starter.train_epoch, model, loader, optimizer, criterion, torch.device("cpu")
    )
    assert result["count"] == 3
    assert result["loss"] == pytest.approx(expected)


def test_train_epoch_clears_stale_gradients_before_update() -> None:
    model = nn.Linear(2, 2)
    reference = deepcopy(model)
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0]])
    y = torch.tensor([0, 1])
    criterion = nn.CrossEntropyLoss()
    expected_optimizer = torch.optim.SGD(reference.parameters(), lr=0.1)
    criterion(reference(x), y).backward()
    expected_optimizer.step()
    for parameter in model.parameters():
        parameter.grad = torch.full_like(parameter, 1000.0)
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x, y), batch_size=2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    exercise_call(starter.train_epoch, model, loader, optimizer, criterion, torch.device("cpu"))
    assert all(
        torch.allclose(actual, expected)
        for actual, expected in zip(model.parameters(), reference.parameters(), strict=True)
    )


def test_validation_does_not_update_weights_or_leave_training_mode() -> None:
    model = ForwardModeProbe()
    model.train()
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0], [0.2, 0.8]])
    y = torch.tensor([0, 1, 0])
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x, y), batch_size=2)
    before = [p.detach().clone() for p in model.parameters()]
    result = exercise_call(
        starter.validate_epoch, model, loader, nn.CrossEntropyLoss(), torch.device("cpu")
    )
    assert result["count"] == 3
    assert 0 <= result["accuracy"] <= 1
    assert result["loss"] >= 0
    assert not model.training
    assert model.forward_modes == [(False, False), (False, False)]
    assert all(torch.equal(a, b) for a, b in zip(before, model.parameters(), strict=True))


def test_error_analysis_uses_real_ids_and_wrong_predictions_only() -> None:
    rows = exercise_call(
        starter.analyze_errors,
        torch.tensor([[3.0, 1.0], [0.1, 2.0], [1.0, 1.0]]),
        torch.tensor([0, 0, 1]),
        ["item-a", "item-b", "item-c"],
    )
    assert rows == [
        {"id": "item-b", "actual": 0, "predicted": 1},
        {"id": "item-c", "actual": 1, "predicted": 0},
    ]


def test_checkpoint_roundtrip_restores_predictions(tmp_path: Path) -> None:
    model = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9)
    inputs = torch.tensor([[0.5, 0.2], [0.1, 0.8]])
    labels = torch.tensor([0, 1])
    nn.CrossEntropyLoss()(model(inputs), labels).backward()
    optimizer.step()
    optimizer.zero_grad()
    assert optimizer.state
    expected_weights = deepcopy(model.state_dict())
    expected_optimizer = deepcopy(optimizer.state_dict())
    path = tmp_path / "student.pt"
    metadata = {"seed": 23, "epoch": 2, "train_ids": ["a", "b"], "validation_ids": ["c"]}
    exercise_call(starter.save_checkpoint, path, model, optimizer, metadata)
    assert path.is_file()
    expected = model(inputs).detach().clone()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.add_(100)
    optimizer.param_groups[0]["lr"] = 999.0
    for state in optimizer.state.values():
        state["momentum_buffer"].fill_(999.0)
    restored = exercise_call(starter.load_checkpoint, path, model, optimizer, torch.device("cpu"))
    assert restored == metadata
    assert torch.allclose(model(inputs).detach(), expected)
    for name, expected_tensor in expected_weights.items():
        assert torch.equal(model.state_dict()[name], expected_tensor)
    actual_optimizer = optimizer.state_dict()
    assert actual_optimizer["param_groups"] == expected_optimizer["param_groups"]
    assert actual_optimizer["state"].keys() == expected_optimizer["state"].keys()
    for parameter_id, state in expected_optimizer["state"].items():
        assert torch.equal(
            actual_optimizer["state"][parameter_id]["momentum_buffer"],
            state["momentum_buffer"],
        )


def test_predict_returns_one_class_per_row_without_gradients() -> None:
    model = ForwardModeProbe()
    model.train()
    rows = torch.tensor([[0.0, 1.0], [1.0, 0.0], [0.2, 0.8]])
    result = exercise_call(starter.predict_classes, model, rows, torch.device("cpu"))
    assert model.forward_modes == [(False, False)]
    assert not model.training
    with torch.no_grad():
        expected = model(rows).argmax(dim=1).tolist()
    assert result == expected
    assert all(isinstance(label, int) for label in result)


def _validate_checkpoint_artifact(
    path: Path, model: Any, optimizer: Any, payload: dict[str, Any]
) -> None:
    """Acceptance-only verifier using a fresh model and an operational optimizer."""
    try:
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise ValueError("checkpoint cannot be loaded with weights_only=True") from exc
    if not isinstance(checkpoint, dict) or set(checkpoint) != {
        "model_state",
        "optimizer_state",
        "metadata",
    }:
        raise ValueError("checkpoint must contain state dictionaries and metadata")
    model_state = checkpoint["model_state"]
    optimizer_state = checkpoint["optimizer_state"]
    metadata = checkpoint["metadata"]
    if not isinstance(model_state, dict) or not model_state:
        raise ValueError("model_state must be a nonempty dictionary")
    if not all(
        isinstance(key, str) and isinstance(value, torch.Tensor)
        for key, value in model_state.items()
    ):
        raise ValueError("model_state requires named tensors")
    if not isinstance(optimizer_state, dict) or set(optimizer_state) != {"state", "param_groups"}:
        raise ValueError("optimizer_state must be an optimizer state dictionary")
    if not isinstance(optimizer_state["state"], dict) or not optimizer_state["state"]:
        raise ValueError("optimizer_state must contain populated momentum state")
    if (
        not isinstance(optimizer_state["param_groups"], list)
        or len(optimizer_state["param_groups"]) != 1
    ):
        raise ValueError("optimizer_state must contain one parameter group")
    if not isinstance(metadata, dict) or any(
        metadata.get(key) != expected
        for key, expected in (
            ("seed", payload["seed"]),
            ("epoch", payload["config"]["epochs"]),
            ("train_ids", payload["train_ids"]),
            ("validation_ids", payload["validation_ids"]),
        )
    ):
        raise ValueError("metadata does not match report")
    try:
        model.load_state_dict(model_state, strict=True)
        optimizer.load_state_dict(optimizer_state)
    except (RuntimeError, TypeError, ValueError, KeyError) as exc:
        raise ValueError("model or optimizer state cannot load into learner architecture") from exc
    group = optimizer.param_groups[0]
    if (
        group["lr"] != payload["config"]["learning_rate"]
        or group["momentum"] != payload["config"]["momentum"]
    ):
        raise ValueError("optimizer hyperparameters do not match report")
    if not all(
        isinstance(state.get("momentum_buffer"), torch.Tensor) for state in optimizer.state.values()
    ):
        raise ValueError("optimizer momentum buffers are missing")
    model.train()
    inputs = torch.zeros((2, payload["config"]["input_dim"]), dtype=torch.float32)
    logits = model(inputs)
    if logits.shape != (2, payload["config"]["n_classes"]) or not torch.isfinite(logits).all():
        raise ValueError("model checkpoint does not match input or class dimensions")
    try:
        optimizer.zero_grad()
        nn.CrossEntropyLoss()(logits, torch.tensor([0, 1])).backward()
        optimizer.step()
    except (RuntimeError, TypeError, ValueError, KeyError) as exc:
        raise ValueError("optimizer checkpoint cannot perform a training step") from exc


def test_submitted_checkpoint_is_safe_state_dict_artifact() -> None:
    validate_report = import_module("labs.01_pytorch_foundations.report").validate_report
    report_path = Path(__file__).resolve().parents[2] / "generated-reports/pytorch/report.json"
    if not report_path.is_file():
        pytest.xfail("Learner checkpoint/report has not been submitted")
    payload = validate_report(report_path)
    checkpoint_path = Path(__file__).resolve().parents[2] / payload["checkpoint"]
    config = payload["config"]
    model = exercise_call(
        starter.build_model, input_dim=config["input_dim"], n_classes=config["n_classes"]
    )
    optimizer = torch.optim.SGD(
        model.parameters(), lr=config["learning_rate"], momentum=config["momentum"]
    )
    _validate_checkpoint_artifact(checkpoint_path, model, optimizer, payload)


def test_checkpoint_artifact_accepts_loadable_state(tmp_path: Path) -> None:
    model = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9)
    x = torch.tensor([[1.0, 0.0]])
    nn.CrossEntropyLoss()(model(x), torch.tensor([1])).backward()
    optimizer.step()
    payload = {
        "seed": 23,
        "train_ids": ["a", "b"],
        "validation_ids": ["c"],
        "config": {
            "input_dim": 2,
            "n_classes": 2,
            "epochs": 2,
            "learning_rate": 0.1,
            "momentum": 0.9,
        },
    }
    checkpoint = {
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "metadata": {"seed": 23, "epoch": 2, "train_ids": ["a", "b"], "validation_ids": ["c"]},
    }
    path = tmp_path / "valid.pt"
    torch.save(checkpoint, path)
    target = nn.Linear(2, 2)
    target_optimizer = torch.optim.SGD(target.parameters(), lr=0.1, momentum=0.9)
    _validate_checkpoint_artifact(path, target, target_optimizer, payload)


@pytest.mark.parametrize(
    "corruption", ["model_string", "optimizer_none", "wrong_shape", "metadata"]
)
def test_checkpoint_artifact_rejects_malformed_state(tmp_path: Path, corruption: str) -> None:
    model = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9)
    x = torch.tensor([[1.0, 0.0]])
    nn.CrossEntropyLoss()(model(x), torch.tensor([1])).backward()
    optimizer.step()
    payload = {
        "seed": 23,
        "train_ids": ["a", "b"],
        "validation_ids": ["c"],
        "config": {
            "input_dim": 2,
            "n_classes": 2,
            "epochs": 2,
            "learning_rate": 0.1,
            "momentum": 0.9,
        },
    }
    checkpoint = {
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "metadata": {"seed": 23, "epoch": 2, "train_ids": ["a", "b"], "validation_ids": ["c"]},
    }
    if corruption == "model_string":
        checkpoint["model_state"] = "truthy"
    elif corruption == "optimizer_none":
        checkpoint["optimizer_state"] = None
    elif corruption == "wrong_shape":
        checkpoint["model_state"] = nn.Linear(3, 2).state_dict()
    else:
        checkpoint["metadata"] = {
            "seed": 999,
            "epoch": 2,
            "train_ids": ["a", "b"],
            "validation_ids": ["c"],
        }
    path = tmp_path / "malformed.pt"
    torch.save(checkpoint, path)
    target = nn.Linear(2, 2)
    target_optimizer = torch.optim.SGD(target.parameters(), lr=0.1, momentum=0.9)
    with pytest.raises(ValueError, match=r"checkpoint|model|optimizer|metadata"):
        _validate_checkpoint_artifact(path, target, target_optimizer, payload)
