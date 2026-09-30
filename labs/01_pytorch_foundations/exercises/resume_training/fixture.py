"""CPU training harness (no learner capture/restore implementation)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
import random
import socket
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.optim import Optimizer
from torch.utils.data import DataLoader, TensorDataset

from .starter import TrainingCursor, restore_state

PACKAGE = "labs.01_pytorch_foundations.exercises.resume_training"
REPOSITORY = Path(__file__).resolve().parents[4]
TRAIN_IDS = tuple(f"object-{i:02}" for i in range(10))
VALIDATION_IDS = ("object-10", "object-11")
SNAPSHOT = [
    {"id": f"object-{i:02}", "features": [i / 12, (i % 3) / 3, (-1.0) ** i, 0.5], "label": i % 2}
    for i in range(12)
]
CONFIG = {
    "seed": 23,
    "batch_size": 3,
    "lr": 0.03,
    "momentum": 0.8,
    "dropout": 0.25,
    "device": "cpu",
    "num_workers": 0,
}
SPLIT = {"train": list(TRAIN_IDS), "validation": list(VALIDATION_IDS)}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


IDENTITY = {
    name: hashlib.sha256(canonical_bytes(value)).hexdigest()
    for name, value in (("data", SNAPSHOT), ("split", SPLIT), ("config", CONFIG))
}


def save_checkpoint(path: Path, state: Mapping[str, Any]) -> None:
    """Create a new artifact; never overwrite a learner checkpoint."""
    with path.open("xb") as destination:
        torch.save(dict(state), destination)


def load_checkpoint(path: Path) -> dict[str, Any]:
    """Load only tensors/primitives, explicitly on CPU."""
    try:
        state = torch.load(path, map_location="cpu", weights_only=True)
    except (OSError, RuntimeError, EOFError, pickle.UnpicklingError, ValueError) as exc:
        raise ValueError("invalid or unsafe checkpoint") from exc
    if not isinstance(state, dict):
        raise ValueError("checkpoint must be a mapping")
    return state


def build_model() -> nn.Sequential:
    return nn.Sequential(nn.Linear(4, 6), nn.ReLU(), nn.Dropout(0.25), nn.Linear(6, 2))


def new_run(seed: int = 23) -> tuple[nn.Module, Optimizer, TrainingCursor]:
    torch.set_num_threads(1)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    model = build_model()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.03, momentum=0.8)
    order = list(TRAIN_IDS)
    random.shuffle(order)
    return model, optimizer, TrainingCursor(0, 0, tuple(order), 0)


def batch_loader(x: torch.Tensor, y: torch.Tensor) -> DataLoader[Any]:
    """Iterator base-seed bookkeeping is independent of dropout's global RNG."""
    return DataLoader(
        TensorDataset(x, y),
        batch_size=3,
        shuffle=False,
        num_workers=0,
        generator=torch.Generator().manual_seed(0),
    )


def advance(
    model: nn.Module,
    optimizer: Optimizer,
    cursor: TrainingCursor,
    until: int,
) -> tuple[TrainingCursor, list[dict[str, Any]]]:
    """Train explicit order, preserving final partial batch and exhausted epoch cursor."""
    rows = {row["id"]: row for row in SNAPSHOT}
    trace = []
    model.train()
    while cursor.global_step < until:
        if cursor.next_batch_offset == len(TRAIN_IDS):
            order = list(TRAIN_IDS)
            random.shuffle(order)
            cursor = TrainingCursor(cursor.epoch + 1, cursor.global_step, tuple(order), 0)
        ids = cursor.sample_order[cursor.next_batch_offset : cursor.next_batch_offset + 3]
        x = torch.tensor([rows[i]["features"] for i in ids], dtype=torch.float32)
        y = torch.tensor([rows[i]["label"] for i in ids], dtype=torch.int64)
        # Both global RNGs affect learning, not merely metadata. Torch also drives dropout.
        x = x * (0.95 + random.random() * 0.1) + float(np.random.normal(0, 0.015))
        loader = batch_loader(x, y)
        batch_x, batch_y = next(iter(loader))
        optimizer.zero_grad()
        loss = nn.functional.cross_entropy(model(batch_x), batch_y)
        loss.backward()  # type: ignore[no-untyped-call]  # Torch 2.14 CPU stub boundary.
        optimizer.step()
        cursor = TrainingCursor(
            cursor.epoch,
            cursor.global_step + 1,
            cursor.sample_order,
            cursor.next_batch_offset + len(ids),
        )
        trace.append(
            {
                "epoch": cursor.epoch,
                "global_step": cursor.global_step,
                "ids": list(ids),
                "loss": float(loss.detach()),
            }
        )
    return cursor, trace


def inference(model: nn.Module) -> dict[str, Any]:
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor([r["features"] for r in SNAPSHOT[-2:]], dtype=torch.float32))
    return {"ids": list(VALIDATION_IDS), "logits": logits}


def result(
    model: nn.Module,
    optimizer: Optimizer,
    cursor: TrainingCursor,
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    """Observation only: next draws are NOT RNG states and cannot resume training."""
    return {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "cursor": asdict(cursor),
        "trace": trace,
        "identity": dict(IDENTITY),
        "inference": inference(model),
        "pid": os.getpid(),
        "next_rng": [random.random(), float(np.random.random()), float(torch.rand(()))],
    }


def assert_same(left: Any, right: Any) -> None:
    """Compare exact structure/IDs/integers and float32 numerical observations."""
    if isinstance(left, torch.Tensor):
        torch.testing.assert_close(left, right, rtol=1e-5, atol=1e-6)
    elif isinstance(left, dict):
        assert isinstance(right, dict)
        assert left.keys() == right.keys()
        for key in left:
            assert_same(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert isinstance(right, (tuple, list))
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            assert_same(a, b)
    elif isinstance(left, float):
        assert isinstance(right, (float, int))
        assert math.isfinite(right)
        assert math.isclose(left, right, rel_tol=1e-5, abs_tol=1e-6)
    else:
        assert type(left) is type(right)
        assert left == right


def fresh_run(output: Path, *, checkpoint: Path | None = None) -> dict[str, Any]:
    command = [sys.executable, "-m", f"{PACKAGE}.fixture", "--output", str(output.resolve())]
    if checkpoint is not None:
        command += ["--checkpoint", str(checkpoint.resolve())]
    completed = subprocess.run(command, cwd=REPOSITORY, capture_output=True, text=True, timeout=60)
    if completed.returncode:
        raise RuntimeError(f"fresh process failed ({completed.returncode}): {completed.stderr}")
    return load_checkpoint(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()

    def deny(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Resume fixture is CPU/offline")

    socket.socket.connect = deny  # type: ignore[method-assign]
    socket.socket.connect_ex = deny  # type: ignore[assignment,method-assign]
    socket.create_connection = deny  # type: ignore[assignment]
    model, optimizer, cursor = new_run(999 if args.checkpoint else 23)
    if args.checkpoint:
        cursor = restore_state(model, optimizer, load_checkpoint(args.checkpoint), IDENTITY)
    cursor, trace = advance(model, optimizer, cursor, 7)
    save_checkpoint(args.output, result(model, optimizer, cursor, trace))


if __name__ == "__main__":
    main()
