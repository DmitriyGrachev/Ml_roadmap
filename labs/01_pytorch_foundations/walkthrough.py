"""Fixed teacher experiments; never imports learner code or generates a submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any, cast

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

from .example import ShapeImages, ShapeNet


def manual_step() -> dict[str, Any]:
    """One hand-configured image, six selected derivatives, one plain SGD step."""
    with torch.random.fork_rng(devices=[]):
        model = ShapeNet().double()
        first = cast(nn.Linear, model.layers[1])
        last = cast(nn.Linear, model.layers[3])
        with torch.no_grad():
            for initial_parameter in model.parameters():
                initial_parameter.zero_()
            first.weight[0, 1] = 1.0
            last.weight[0, 0] = 1.0
        image = torch.zeros((1, 1, 4, 4), dtype=torch.float64)
        image.flatten()[1] = 1.0
        target = torch.tensor([0], dtype=torch.int64)
        flat = image.flatten(start_dim=1)
        preactivation = first(flat)
        hidden = torch.relu(preactivation)
        logits = model(image)
        loss = nn.functional.cross_entropy(logits, target)
        torch.autograd.backward(loss)
        selected = {
            "w1": (first.weight, (0, 1)),
            "b1": (first.bias, (0,)),
            "w20": (last.weight, (0, 0)),
            "b20": (last.bias, (0,)),
            "w21": (last.weight, (1, 0)),
            "b21": (last.bias, (1,)),
        }
        gradients = {}
        for name, (parameter, index) in selected.items():
            assert parameter.grad is not None
            gradients[name] = float(parameter.grad[index])

        # Independent central-difference check at a smooth coordinate; not autograd.
        epsilon = 1e-5
        with torch.no_grad():
            last.weight[0, 0] = 1.0 + epsilon
            upper = nn.functional.cross_entropy(model(image), target).item()
            last.weight[0, 0] = 1.0 - epsilon
            lower = nn.functional.cross_entropy(model(image), target).item()
            last.weight[0, 0] = 1.0
        torch.autograd.backward(nn.functional.cross_entropy(model(image), target))
        assert last.weight.grad is not None
        accumulated = last.weight.grad[0, 0].item()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        optimizer.zero_grad(set_to_none=True)
        cleared = all(parameter.grad is None for parameter in model.parameters())
        torch.autograd.backward(nn.functional.cross_entropy(model(image), target))
        optimizer.step()
        with torch.no_grad():
            loss_after = nn.functional.cross_entropy(model(image), target).item()
        return {
            "shapes": {
                "image": list(image.shape),
                "flat": list(flat.shape),
                "hidden": list(hidden.shape),
                "logits": list(logits.shape),
                "target": list(target.shape),
                "loss": list(loss.shape),
            },
            "target_dtype": str(target.dtype),
            "input_dtype": str(image.dtype),
            "device": str(image.device),
            "preactivation": preactivation.detach().tolist(),
            "hidden": hidden.detach().tolist(),
            "logits": logits.detach().tolist(),
            "probabilities": logits.detach().softmax(dim=1).tolist(),
            "loss": loss.item(),
            "gradients": gradients,
            "finite_difference_w20": (upper - lower) / (2 * epsilon),
            "accumulated_w20": accumulated,
            "cleared_to_none": cleared,
            "after": {
                name: parameter[index].item() for name, (parameter, index) in selected.items()
            },
            "loss_after": loss_after,
            "logging_detached": not loss.detach().requires_grad,
        }


def mode_probe() -> dict[str, Any]:
    """Observe the two independent switches, with a fresh tiny dropout module."""
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(29)
        model = nn.Sequential(nn.Dropout(0.5), nn.Linear(4, 2))
        inputs = torch.ones((2, 4))
        model.eval()
        with torch.enable_grad():
            eval_tracks_grad = model(inputs).requires_grad
        model.train()
        with torch.no_grad():
            train_output = model(inputs)
            train_mode = model.training
        model.eval()
        with torch.no_grad():
            output = model(inputs)
            repeated = model(inputs)
        return {
            "eval_tracks_grad": eval_tracks_grad,
            "train_no_grad_training": train_mode,
            "train_no_grad_tracks_grad": train_output.requires_grad,
            "eval_no_grad_tracks_grad": output.requires_grad,
            "eval_repeated_max_difference": (output - repeated).abs().max().item(),
        }


def _shape_training(directory: Path) -> dict[str, Any]:
    """Instrument the existing teacher fixture, not a general train_epoch solution."""
    torch.manual_seed(13)
    dataset = ShapeImages()
    train = DataLoader(
        Subset(dataset, list(range(19))),
        batch_size=6,
        shuffle=True,
        generator=torch.Generator().manual_seed(13),
    )
    validation = DataLoader(
        Subset(dataset, list(range(19, 26))),
        batch_size=3,
        generator=torch.Generator().manual_seed(29),
    )
    model = ShapeNet().to("cpu")
    optimizer = torch.optim.SGD(model.parameters(), lr=0.15)
    criterion = nn.CrossEntropyLoss()
    epochs: list[dict[str, Any]] = []
    for epoch in range(4):
        model.train()
        steps: list[dict[str, Any]] = []
        for images, labels in train:
            before = nn.utils.parameters_to_vector(model.parameters()).detach().clone()
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            gradients = [p.grad.flatten() for p in model.parameters() if p.grad is not None]
            gradient_norm = torch.cat(gradients).norm().item()
            optimizer.step()
            after = nn.utils.parameters_to_vector(model.parameters()).detach()
            steps.append(
                {
                    "count": len(labels),
                    "loss": loss.item(),
                    "gradient_norm": gradient_norm,
                    "parameter_delta": (after - before).norm().item(),
                    "training": model.training,
                    "grad_enabled": torch.is_grad_enabled(),
                }
            )
        model.eval()
        before_validation = nn.utils.parameters_to_vector(model.parameters()).detach().clone()
        row_losses: list[float] = []
        predictions: list[int] = []
        truth: list[int] = []
        validation_modes: list[list[bool]] = []
        with torch.no_grad():
            for images, labels in validation:
                validation_modes.append([model.training, torch.is_grad_enabled()])
                logits = model(images)
                row_losses.extend(
                    nn.functional.cross_entropy(logits, labels, reduction="none").tolist()
                )
                predictions.extend(logits.argmax(dim=1).tolist())
                truth.extend(labels.tolist())
        after_validation = nn.utils.parameters_to_vector(model.parameters()).detach()
        epochs.append(
            {
                "epoch": epoch + 1,
                "steps": steps,
                "train_count": 19,
                "validation_count": 7,
                "train_loss": sum(step["loss"] * step["count"] for step in steps) / 19,
                "validation_loss": sum(row_losses) / 7,
                "validation_row_losses": row_losses,
                "validation_accuracy": sum(a == b for a, b in zip(predictions, truth, strict=True))
                / 7,
                "validation_modes": validation_modes,
                "validation_parameter_delta": (after_validation - before_validation).norm().item(),
            }
        )
    # Same model-only inference format as example.py, not a new resume format.
    checkpoint = directory / "shape-smoke.pt"
    torch.save({"model_state": model.state_dict(), "epoch": 4}, checkpoint)
    restored = ShapeNet()
    restored.load_state_dict(
        torch.load(checkpoint, map_location="cpu", weights_only=True)["model_state"]
    )
    restored.eval()
    validation_images = torch.stack(dataset.images[19:])
    with torch.inference_mode():
        original_logits = model(validation_images)
        restored_logits = restored(validation_images)
    snapshot = {
        "name": "teacher ShapeImages seed41",
        "images": torch.stack(dataset.images).tolist(),
        "labels": dataset.labels,
        "train_indices": list(range(19)),
        "validation_indices": list(range(19, 26)),
    }
    snapshot_bytes = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    (directory / "snapshot.json").write_bytes(snapshot_bytes)
    return {
        "seed": 13,
        "epochs": epochs,
        "train_batch_sizes": [step["count"] for step in steps],
        "validation_batch_sizes": [len(labels) for _, labels in validation],
        "config": {
            "device": "cpu",
            "dtype": "float32",
            "optimizer": "SGD",
            "learning_rate": 0.15,
            "epochs": 4,
            "batch_size": 6,
        },
        "dataset_split_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
        "predictions": restored_logits.argmax(dim=1).tolist(),
        "labels": dataset.labels[19:],
        "reload_max_abs_difference": (restored_logits - original_logits).abs().max().item(),
    }


def run_walkthrough(directory: Path, *, plots: bool = False) -> dict[str, Any]:
    """Write a fresh teacher-only run. Existing directories are never reused."""
    directory.mkdir(parents=True, exist_ok=False)
    with torch.random.fork_rng(devices=[]):
        result: dict[str, Any] = {
            "evidence": "TEACHER_CPU_MECHANICS_ONLY",
            "quality_claim": False,
            "versions": {"python": platform.python_version(), "torch": torch.__version__},
            "source_sha256": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (Path(__file__), Path(__file__).with_name("example.py"))
            },
            "manual": manual_step(),
            "modes": mode_probe(),
            "training": _shape_training(directory),
            "plots": ["learning.png"] if plots else [],
        }
    if plots:
        from matplotlib.figure import Figure

        figure = Figure(figsize=(7.2, 4.4), layout="constrained")
        axis = figure.subplots()
        epochs = result["training"]["epochs"]
        numbers = [row["epoch"] for row in epochs]
        axis.plot(
            numbers, [row["train_loss"] for row in epochs], "o-", label="Train batches (online)"
        )
        axis.plot(
            numbers,
            [row["validation_loss"] for row in epochs],
            "s-",
            label="Validation (epoch end)",
        )
        axis.set(
            xlabel="Epoch",
            ylabel="Mean cross-entropy (nats)",
            title="Synthetic shapes: mechanism check, not a quality benchmark",
            xticks=numbers,
        )
        axis.legend()
        axis.grid(alpha=0.25)
        figure.savefig(directory / "learning.png", dpi=150)
    (directory / "trace.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    arguments = parser.parse_args()
    result = run_walkthrough(arguments.output, plots=arguments.plots)
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "quality_claim": result["quality_claim"],
                "manual_loss": result["manual"]["loss"],
                "reload_difference": result["training"]["reload_max_abs_difference"],
            }
        )
    )


if __name__ == "__main__":
    main()
