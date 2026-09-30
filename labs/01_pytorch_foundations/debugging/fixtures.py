"""CPU evidence instrumentation for the supplied cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import runpy
from pathlib import Path
from typing import Any

import torch
from torch import nn

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity

PACKAGE = "labs.01_pytorch_foundations.debugging"
CASE_IDS = ("a", "b", "c", "d")
SNAPSHOT = [
    {
        "id": f"sample-{i}",
        "x": [[float(i + 1), 0.5], [0.25, float(i + 1)]],
        "y": [[float(i) / 3], [0.5]],
        "mask": [[True], [i % 2 == 0]],
    }
    for i in range(6)
]
SPLIT = {"train": [r["id"] for r in SNAPSHOT[:4]], "validation": [r["id"] for r in SNAPSHOT[4:]]}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_same(left: Any, right: Any) -> None:
    """Compare replay tensors, including observed nonfinite failures."""
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)
    elif isinstance(left, dict):
        assert isinstance(right, dict)
        assert left.keys() == right.keys()
        for key in left:
            assert_same(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert isinstance(right, type(left))
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            assert_same(a, b)
    else:
        assert left == right


def _parameters(model: nn.Module) -> torch.Tensor:
    return torch.cat([p.detach().flatten().clone() for p in model.parameters()])


def observe(source: Path, *, seed: int) -> dict[str, Any]:
    """Execute an explicitly trusted local source, recording actual CPU operations.

    This is code execution, not a sandbox. A JSON field never selects this source.
    """
    namespace = runpy.run_path(str(source))
    config = namespace["CONFIG"]
    if set(config) != {"lr", "steps"} or config["steps"] != 8:
        raise ValueError("config requires lr and eight steps")
    if not isinstance(config["lr"], (float, int)) or not 0 < config["lr"] < float("inf"):
        raise ValueError("lr must be positive and finite")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model = nn.Sequential(nn.Dropout(0.3), nn.Linear(2, 1))
        optimizer = torch.optim.SGD(model.parameters(), lr=config["lr"])
        x = torch.tensor([r["x"] for r in SNAPSHOT], dtype=torch.float32)
        y = torch.tensor([r["y"] for r in SNAPSHOT], dtype=torch.float32)
        mask = torch.tensor([r["mask"] for r in SNAPSHOT], dtype=torch.bool)
        trace = []
        for index in range(config["steps"]):
            row: dict[str, Any] = {
                "step": index,
                "ids": SPLIT["train"],
                "before": _parameters(model),
            }
            calls: list[dict[str, bool]] = []
            dropout_calls: list[dict[str, Any]] = []
            observed_outputs: list[torch.Tensor] = []

            def capture(
                module: nn.Module,
                inputs: Any,
                output: Any,
                calls: list[dict[str, bool]] = calls,
                observed_outputs: list[torch.Tensor] = observed_outputs,
            ) -> None:
                calls.append({"training": module.training, "grad_enabled": torch.is_grad_enabled()})
                observed_outputs.append(output.detach().clone())

            def capture_dropout(
                module: nn.Module,
                inputs: Any,
                dropout_calls: list[dict[str, Any]] = dropout_calls,
            ) -> None:
                assert isinstance(module, nn.Dropout)
                dropout_calls.append({"training": module.training, "p": module.p})

            hook = model.register_forward_hook(capture)
            dropout_hooks = [
                child.register_forward_pre_hook(capture_dropout)
                for child in model.modules()
                if isinstance(child, nn.Dropout)
            ]
            try:
                prediction, loss = namespace["step"](model, optimizer, x[:4], y[:4], mask[:4])
                row["prediction"] = prediction.detach().clone()
                row["loss"] = loss.detach().clone()
                row["error"] = None
            except (RuntimeError, ValueError) as exc:
                row["error"] = {"type": type(exc).__name__, "message": str(exc)}
            finally:
                hook.remove()
                for dropout_hook in dropout_hooks:
                    dropout_hook.remove()
            row["step_calls"] = calls.copy()
            row["step_dropout_calls"] = dropout_calls
            row["train_outputs"] = observed_outputs.copy()
            observed_outputs.clear()
            calls.clear()
            row["after"] = _parameters(model)
            row["gradients"] = [
                None if p.grad is None else p.grad.detach().clone() for p in model.parameters()
            ]
            hook = model.register_forward_hook(capture)
            try:
                with torch.random.fork_rng(devices=[]):
                    outputs = [namespace["validate"](model, x[4:]) for _ in range(2)]
                row["validation"] = {
                    "ids": SPLIT["validation"],
                    "outputs": [o.detach().clone() for o in outputs],
                    "requires_grad": [o.requires_grad for o in outputs],
                    "calls": calls,
                }
            finally:
                hook.remove()
            trace.append(row)
            if row["error"] is not None:
                break
    return {"seed": seed, "config": config, "trace": trace}


def run_variant(case_id: str, source: Path, output_dir: Path, *, seed: int) -> Path:
    """Explicit code-execution entry point for a learner-owned local module."""
    if case_id not in CASE_IDS:
        raise ValueError("unknown case")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("seed must be an unsigned 32-bit integer")
    if output_dir.exists():
        raise FileExistsError(output_dir)
    source_bytes = source.read_bytes()
    run = dict(observe(source, seed=seed), case_id=case_id)
    output_dir.mkdir(parents=True, exist_ok=False)
    files = {
        "snapshot.json": canonical(SNAPSHOT),
        "split.json": canonical(SPLIT),
        "source.py": source_bytes,
    }
    for name, content in files.items():
        (output_dir / name).write_bytes(content)
    with (output_dir / "trace.pt").open("xb") as stream:
        torch.save(run, stream)
    manifest = {
        "schema_version": 1,
        "exercise_id": "lab-training-diagnostics",
        "dataset_sha256": digest(files["snapshot.json"]),
        "split_sha256": digest(files["split.json"]),
        "config": run["config"],
        "case_id": case_id,
        "seed": seed,
        "artifacts": {
            name: digest((output_dir / name).read_bytes()) for name in (*files, "trace.pt")
        },
    }
    (output_dir / "manifest.json").write_bytes(canonical(manifest))
    return output_dir


def run_case(case_id: str, output_dir: Path, *, seed: int) -> Path:
    if case_id not in CASE_IDS:
        raise ValueError("unknown case")
    return run_variant(
        case_id, Path(__file__).with_name(f"case_{case_id}.py"), output_dir, seed=seed
    )


def load_run(root: Path) -> dict[str, Any]:
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        validate_identity(
            manifest,
            exercise_id="lab-training-diagnostics",
            dataset_sha256=digest(canonical(SNAPSHOT)),
            split_sha256=digest(canonical(SPLIT)),
        )
        paths = {
            name: checked_artifact(root, name, manifest["artifacts"][name])
            for name in ("snapshot.json", "split.json", "source.py", "trace.pt")
        }
        assert paths["snapshot.json"].read_bytes() == canonical(SNAPSHOT)
        assert paths["split.json"].read_bytes() == canonical(SPLIT)
        run = torch.load(paths["trace.pt"], weights_only=True, map_location="cpu")
        assert isinstance(run, dict)
        for key in ("case_id", "seed", "config"):
            assert_same(run[key], manifest[key])
        assert run["case_id"] in CASE_IDS
        assert type(run["seed"]) is int
        assert 0 <= run["seed"] < 2**32
        assert isinstance(run["trace"], list)
        assert run["trace"]
    except (
        OSError,
        UnicodeError,
        ValueError,
        KeyError,
        TypeError,
        AssertionError,
        RuntimeError,
        EOFError,
        pickle.UnpicklingError,
    ) as exc:
        raise ValueError("invalid run evidence") from exc
    return run


def assert_healthy(run: dict[str, Any]) -> None:
    """Behavior contract, without an accuracy target or a repair implementation."""
    assert len(run["trace"]) == 8, "incomplete training trace"
    y = torch.tensor([r["y"] for r in SNAPSHOT[:4]], dtype=torch.float32)
    mask = torch.tensor([r["mask"] for r in SNAPSHOT[:4]], dtype=torch.bool)
    for row in run["trace"]:
        assert row["error"] is None, "training raised an exception"
        assert row["step_calls"], "step did not execute the model"
        assert all(c["training"] and c["grad_enabled"] for c in row["step_calls"]), (
            "training context is incorrect during actual learner forward"
        )
        assert row["step_dropout_calls"], "training stochasticity: no dropout forward observed"
        assert all(c["training"] and 0 < c["p"] < 1 for c in row["step_dropout_calls"]), (
            "training stochasticity disabled during actual learner forward"
        )
        assert row["prediction"].shape == y.shape, "prediction/target shapes differ"
        assert row["loss"].ndim == 0, "nonscalar loss"
        assert torch.isfinite(row["loss"]), "nonfinite loss"
        expected = (row["prediction"][mask] - y[mask]).square().mean()
        torch.testing.assert_close(row["loss"], expected)
        assert all(g is not None and torch.isfinite(g).all() for g in row["gradients"]), (
            "missing/nonfinite gradients"
        )
        assert torch.isfinite(row["after"]).all(), "nonfinite parameters"
        assert not torch.equal(row["before"], row["after"]), "parameters did not change"
        validation = row["validation"]
        assert len(validation["calls"]) == 2
        assert all(not c["training"] and not c["grad_enabled"] for c in validation["calls"]), (
            "validation context is incorrect"
        )
        assert validation["requires_grad"] == [False, False]
        assert all(p.shape == (2, 2, 1) and torch.isfinite(p).all() for p in validation["outputs"])
        assert torch.equal(*validation["outputs"]), "validation is stochastic"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id", choices=CASE_IDS)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()
    print(run_case(args.case_id, args.output_dir, seed=args.seed))


if __name__ == "__main__":
    main()
