"""Test-owned safe bundles and deterministic I/O adapter; never learner evidence."""

from __future__ import annotations

import platform
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..artifacts import PREPROCESSING, file_sha256, json_bytes, read_json, write_run_new
from ..contracts import validate_dataset, validate_splits
from .demo import STAGES


def make_bundles(output: Path) -> Path:
    fixtures = Path(__file__).parents[1] / "part_a1" / "fixtures"
    dataset = validate_dataset(read_json(fixtures / "data.json"))
    splits = validate_splits(read_json(fixtures / "splits.json"), dataset)
    for method, label in (("rules", "circle"), ("tfidf-linear", "triangle")):
        model = {
            "schema_version": 1,
            "labels": list(dataset.labels),
            "rules": [{"token": "never", "label": label}],
            "fallback_label": label,
        }
        write_run_new(
            output / method,
            data=fixtures / "data.json",
            splits=fixtures / "splits.json",
            sources=fixtures / "sources.json",
            model=json_bytes(model),
            predictions=[{"row_id": row_id, "predicted_label": label} for row_id in splits["test"]],
            manifest={
                "schema_version": 1,
                "exercise_id": "test-owned-lifecycle",
                "dataset_sha256": file_sha256(fixtures / "data.json"),
                "split_sha256": file_sha256(fixtures / "splits.json"),
                "config": {"seed": 1},
                "method": method,
                "evidence_kind": "TEST_OWNED_SYNTHETIC",
                "run_id": f"test-{method}",
                "code": {
                    "revision": "test",
                    "dirty": True,
                    "source_sha256": file_sha256(Path(__file__)),
                },
                "versions": {"python": platform.python_version()},
                "labels": list(dataset.labels),
                "preprocessing": PREPROCESSING,
                "model": {"id": f"test-{method}", "revision": "1", "format": "rules-json-v1"},
            },
            measurement={
                "timings": [
                    {
                        "name": "test-fixture",
                        "value": 0.0,
                        "unit": "seconds",
                        "device": "cpu",
                        "condition": "warm",
                        "sample_count": 1,
                        "batch_size": 1,
                    }
                ],
                "memory_bytes": None,
                "memory_unknown_reason": "Test-owned synthetic fixture",
            },
            selection={"criterion": "test-only fixed model", "selected_method": method},
        )
    return output


class FakeProcess:
    def __init__(self, pid: int, *, rejected: bool) -> None:
        self.pid = pid
        self.returncode: int | None = None
        self.rejected = rejected

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = 3 if self.rejected else 0
        return self.returncode

    def poll(self) -> int | None:
        return self.returncode


class RecordingTransport:
    """Socket-free seam. Records requested bounds, ordering and guaranteed cleanup."""

    def __init__(self, *, fail_stage: str | None = None) -> None:
        self.fail_stage = fail_stage
        self.calls: list[dict[str, Any]] = []
        self.closed: list[int] = []
        self.loads: list[dict[str, Any]] = []
        self.requests: list[dict[str, Any]] = []
        self.current: dict[str, Any] = {}

    @contextmanager
    def child(self, bundle: Path, digest: str, log_path: Path) -> Iterator[tuple[FakeProcess, str]]:
        self.current = {"stage": STAGES[len(self.calls)], "bundle": bundle, "digest": digest}
        self.calls.append(self.current)
        process = FakeProcess(
            100 + len(self.calls), rejected=digest != file_sha256(bundle / "manifest.json")
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "ValueError: manifest verification failed: artifact sha256 differs\n"
            if process.rejected
            else "Test-owned startup ready\n",
            encoding="utf-8",
        )
        try:
            yield process, "http://127.0.0.1:offline-test"
        finally:
            if process.returncode is None:
                process.returncode = -15
            self.closed.append(process.pid)

    def ready(self, process: Any, url: str, digest: str) -> dict[str, Any]:
        if process.rejected:
            raise RuntimeError("bad digest must not become ready")
        return {"ready": True, "bundle_sha256": digest}

    def request(
        self, url: str, payload: dict[str, Any] | None = None, *, timeout: float = 2.0
    ) -> dict[str, Any]:
        self.requests.append(
            {"stage": self.current["stage"], "payload": payload, "timeout": timeout}
        )
        if payload == {"text": " "}:
            return {"status": 422, "payload": None, "outcome": "http_error", "seconds": 0.01}
        bundle = self.current["bundle"]
        manifest = read_json(bundle / "manifest.json")
        model = read_json(bundle / manifest["artifacts"]["model"]["path"])
        return {
            "status": 200,
            "outcome": "ok",
            "seconds": 0.02,
            "payload": {
                "bundle_sha256": self.current["digest"],
                "model_id": manifest["model"]["id"],
                "preprocessing_version": manifest["preprocessing"]["version"],
                "predicted_label": model["fallback_label"],
            },
        }

    def load(
        self, url: str, payload: dict[str, Any], *, count: int, concurrency: int
    ) -> list[dict[str, Any]]:
        self.loads.append(
            {"stage": self.current["stage"], "count": count, "concurrency": concurrency}
        )
        rows = [self.request(url, payload) for _ in range(count)]
        if self.current["stage"] == self.fail_stage:
            rows[0] = {"status": None, "payload": None, "outcome": "timeout", "seconds": 2.0}
        return rows
