"""Manual synthetic CUDA timing/memory experiment, never started by pytest/import."""

import argparse
import json
import time
from pathlib import Path
from typing import Any


def require_cuda(cuda: Any) -> None:
    if not cuda.is_available():
        raise RuntimeError("CUDA unavailable: GPU experiment NOT_RUN")


def run(output: Path, steps: int, amp: bool, checkpoint: bool) -> dict[str, Any]:
    if not 1 <= steps <= 20:
        raise ValueError("steps must be 1..20")
    if output.exists():
        raise ValueError("output must name a new directory")
    import torch
    from torch.utils.checkpoint import checkpoint as recompute

    require_cuda(torch.cuda)
    torch.manual_seed(17)
    model = (
        torch.nn.Sequential(torch.nn.Linear(256, 512), torch.nn.GELU(), torch.nn.Linear(512, 16))
        .cuda()
        .train()
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    x = torch.randn(32, 256, device="cuda")
    y = torch.randn(32, 16, device="cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=amp)

    def step() -> float:
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            pred = recompute(model, x, use_reentrant=False) if checkpoint else model(x)
            loss = torch.nn.functional.mse_loss(pred, y)
        if not torch.isfinite(loss):
            raise ValueError("nonfinite measured loss")
        scaled: Any = scaler.scale(loss)  # upstream Tensor.backward is untyped
        scaled.backward()
        scaler.step(optimizer)
        scaler.update()
        return float(loss.detach())

    step()  # warmup includes optimizer-state allocation
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    baseline = torch.cuda.memory_allocated()
    started = time.perf_counter()
    losses = [step() for _ in range(steps)]
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    report = {
        "status": "MEASURED_CUDA_SYNTHETIC",
        "device": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
        "steps": steps,
        "amp": amp,
        "checkpoint": checkpoint,
        "elapsed_seconds": elapsed,
        "seconds_per_step": elapsed / steps,
        "baseline_allocated_bytes": baseline,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
        "losses": losses,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--checkpoint", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.steps, args.amp, args.checkpoint), indent=2))


if __name__ == "__main__":
    main()
