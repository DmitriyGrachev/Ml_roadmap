"""Measured in-process ASGI restarts A → B → rejected startup → A.

This executes real inference/lifespan, not a network/container benchmark.
"""

from __future__ import annotations

import argparse
import html
import platform
import statistics
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from ..artifacts import file_sha256, json_bytes
from .app import create_app


def _timeline(events: list[dict[str, Any]]) -> str:
    bars = []
    maximum = max(event["startup_seconds"] for event in events)
    for index, event in enumerate(events):
        y = 70 + index * 65
        elapsed = event["startup_seconds"]
        bars.append(
            f'<text x="20" y="{y}">{html.escape(event["stage"])}</text>'
            f'<rect x="130" y="{y - 17}" width="{elapsed / maximum * 200:.2f}" '
            f'height="20" fill="{"#b34e40" if "error" in event else "#36846b"}"/>'
            f'<text x="350" y="{y}">{elapsed * 1000:.3f} ms; '
            f"{html.escape(str(event.get('predicted_label', 'startup rejected')))}</text>"
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="360" '
        'role="img" aria-labelledby="title description">'
        '<title id="title">Observed CPU ASGI startup recovery timeline</title>'
        '<desc id="description">A rules predicts circle; B TF-IDF predicts triangle; '
        "a wrong digest rejects startup; a fresh A predicts circle again. "
        "Bars scale linearly to the maximum measured startup duration.</desc>"
        '<rect width="800" height="360" fill="white"/>'
        '<g font-family="sans-serif" font-size="15" fill="#17212b">'
        f'<text x="20" y="28">Fresh lifespan startup (ms, CPU; '
        f"200 px = {maximum * 1000:.3f} ms)</text>"
        + "".join(bars)
        + '<text x="20" y="345">Sequential teacher smoke; '
        "not throughput or production tail evidence.</text></g></svg>"
    )


def run_recovery(output: Path, *, samples: int = 5) -> Path:
    if output.exists():
        raise FileExistsError(f"recovery output already exists: {output}")
    if type(samples) is not int or not 1 <= samples <= 100:
        raise ValueError("samples must be an integer in 1..100")
    from fastapi.testclient import TestClient

    from ..part_a1.demo import run_demo

    output.mkdir(parents=True, exist_ok=False)
    teacher = run_demo(output / "teacher")
    a, b = teacher / "rules", teacher / "tfidf-linear"
    digests = {root: file_sha256(root / "manifest.json") for root in (a, b)}
    events: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    timeline_started = time.perf_counter()
    for stage, root, digest in (
        ("A", a, digests[a]),
        ("B", b, digests[b]),
        ("failure", b, "0" * 64),
        ("A-restored", a, digests[a]),
    ):
        started = time.perf_counter()
        event: dict[str, Any] = {"stage": stage, "offset_seconds": started - timeline_started}
        try:
            with TestClient(create_app(root, digest, trusted_local_artifact=root == b)) as client:
                event["startup_seconds"] = time.perf_counter() - started
                for index in range(samples):
                    request_started = time.perf_counter()
                    response = client.post("/predict", json={"text": "triangle"})
                    duration = time.perf_counter() - request_started
                    response.raise_for_status()
                    payload = response.json()
                    requests.append(
                        {
                            "stage": stage,
                            "index": index,
                            "condition": "warm_after_startup_replay",
                            "request_position": "first" if index == 0 else "subsequent",
                            "duration_seconds": duration,
                            "status_code": response.status_code,
                            "batch_size": 1,
                            **payload,
                        }
                    )
                event.update(payload)
        except ValueError as exc:
            if stage != "failure":
                raise
            event.update(startup_seconds=time.perf_counter() - started, error=str(exc))
        if stage == "failure" and "error" not in event:
            raise RuntimeError("incorrect digest unexpectedly started")
        events.append(event)
    if events[0]["predicted_label"] != "circle" or events[1]["predicted_label"] != "triangle":
        raise RuntimeError("teacher A and B must exercise different actual inference")
    for key in ("bundle_sha256", "model_id", "preprocessing_version", "predicted_label"):
        if events[0][key] != events[3][key]:
            raise RuntimeError(f"rollback identity/inference mismatch: {key}")
    durations = sorted(row["duration_seconds"] for row in requests)
    report = {
        "evidence_kind": "AUTHOR_SYNTHETIC_ASGI_SMOKE_ONLY",
        "transport": "in-process TestClient",
        "unit": "seconds",
        "device": "cpu",
        "sample_count": len(requests),
        "batch_size": 1,
        "events": events,
        "requests": requests,
        "median_seconds": statistics.median(durations),
        "observed_max_seconds": max(durations),
        "tail_limit": (
            "Tiny sequential sample; maximum is observed, not an estimated production p99."
        ),
        "memory_bytes": None,
        "memory_unknown_reason": "CPU native/process peak memory not instrumented; no GPU used.",
        "versions": {name: version(name) for name in ("fastapi", "starlette", "scikit-learn")},
        "python": platform.python_version(),
        "docker": "NOT_RUN",
        "network_server": "NOT_RUN",
    }
    (output / "recovery.json").write_bytes(json_bytes(report))
    (output / "timeline.svg").write_text(_timeline(events), encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--samples", type=int, default=5)
    args = parser.parse_args()
    print(run_recovery(args.output, samples=args.samples))
