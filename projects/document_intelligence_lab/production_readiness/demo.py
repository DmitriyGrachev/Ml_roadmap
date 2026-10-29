"""Author real localhost TCP lifecycle. Explicit CLI only; no paid/cloud operations."""

from __future__ import annotations

import argparse
import math
import platform
import statistics
import subprocess
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from ..artifacts import file_sha256, json_bytes
from .transport import ChildProcess, LifecycleTransport, LocalTransport

STAGES = ("A", "A-restarted", "B", "rejected", "A-restored")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        duration = row["seconds"]
        if (
            type(duration) not in (int, float)
            or not math.isfinite(duration)
            or duration < 0
            or row["outcome"] not in ("ok", "http_error", "timeout", "transport_error")
        ):
            raise ValueError("invalid measured outcome/duration")
    successes = [r["seconds"] for r in rows if r["outcome"] == "ok"]
    return {
        "attempts": len(rows),
        "successes": len(successes),
        "failures": len(rows) - len(successes),
        "timeouts": sum(r["outcome"] == "timeout" for r in rows),
        "http_errors": sum(r["outcome"] == "http_error" for r in rows),
        "transport_errors": sum(r["outcome"] == "transport_error" for r in rows),
        "median_seconds": statistics.median(successes) if successes else None,
        "observed_max_seconds": max(successes) if successes else None,
    }


def delayed_quality(
    predictions: list[dict[str, Any]], labels: list[dict[str, Any]], *, as_of: int
) -> dict[str, Any]:
    """Join only labels already available at the analysis cutoff; unique IDs required."""
    pred = {p["request_id"]: p for p in predictions if p["predicted_at"] <= as_of}
    truth = {r["request_id"]: r for r in labels if r["available_at"] <= as_of}
    if len({p["request_id"] for p in predictions}) != len(predictions):
        raise ValueError("duplicate prediction request_id")
    if len({r["request_id"] for r in labels}) != len(labels):
        raise ValueError("duplicate label request_id")
    joined = [(p, truth[key]) for key, p in pred.items() if key in truth]
    if any(label["available_at"] < p["predicted_at"] for p, label in joined):
        raise ValueError("label precedes prediction")
    return {
        "labeled_count": len(joined),
        "coverage": len(joined) / len(pred) if pred else 0.0,
        "accuracy": sum(p["prediction"] == label["label"] for p, label in joined) / len(joined)
        if joined
        else None,
    }


def _save_report(output: Path, report: dict[str, Any]) -> None:
    temporary = output / "lifecycle.json.tmp"
    temporary.write_bytes(json_bytes(report))
    temporary.replace(output / "lifecycle.json")


def run_demo(
    output: Path,
    *,
    requests: int = 12,
    concurrency: int = 3,
    transport: LifecycleTransport | None = None,
) -> Path:
    if type(requests) is not int or not 2 <= requests <= 200:
        raise ValueError("requests must be integer in 2..200")
    if type(concurrency) is not int or not 1 <= concurrency <= min(requests, 16):
        raise ValueError("concurrency must be integer in 1..min(requests,16)")
    if output.exists():
        raise FileExistsError(output)
    from ..part_a1.demo import run_demo as train_teacher

    io = transport if transport is not None else LocalTransport()
    output.mkdir(parents=True)
    bundles = train_teacher(output / "bundles")
    roots = {"A": bundles / "rules", "B": bundles / "tfidf-linear"}
    events: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "schema_version": 1,
        "exercise_id": "production-service-lifecycle",
        "evidence_kind": "AUTHOR_LOCAL_TCP_DEMO",
        "transport": "localhost TCP/uvicorn",
        "device": "cpu",
        "unit": "seconds",
        "run_status": "RUNNING",
        "python": platform.python_version(),
        "versions": {name: version(name) for name in ("uvicorn", "fastapi", "scikit-learn")},
        "concurrency": concurrency,
        "requests_per_stage": requests,
        "events": events,
        "bundles": {
            name: {
                "path": root.relative_to(output).as_posix(),
                "manifest_sha256": file_sha256(root / "manifest.json"),
            }
            for name, root in roots.items()
        },
        "cold_definition": "Fresh child imports + bundle load + readiness replay + HTTP ready",
        "warm_definition": "After readiness replay and first request; thread-pool clients",
        "tail_limit": "Observed maximum only; small local sample cannot estimate production p99",
        "timeout_limit": "Client deadline does not prove cancellation of server inference",
        "memory_bytes": None,
        "memory_unknown_reason": "Process/native peak not instrumented",
        "docker": "NOT_RUN",
        "cloud": "NOT_RUN",
        "learner_mastery": "REQUIRES_REVIEW",
    }
    _save_report(output, report)
    try:
        for stage in STAGES:
            name = "B" if stage in ("B", "rejected") else "A"
            root = roots[name]
            digest = "0" * 64 if stage == "rejected" else file_sha256(root / "manifest.json")
            started = time.perf_counter()
            event: dict[str, Any] = {
                "stage": stage,
                "bundle_name": name,
                "bundle_sha256": digest,
                "stage_status": "RUNNING",
            }
            events.append(event)
            process: ChildProcess | None = None
            log_path = output / f"{stage}.log"
            try:
                with io.child(root, digest, log_path) as (process, url):
                    event["pid"] = process.pid
                    if stage == "rejected":
                        try:
                            process.wait(timeout=20)
                        except subprocess.TimeoutExpired as exc:
                            raise RuntimeError("invalid digest did not stop startup") from exc
                        if process.returncode == 0:
                            raise RuntimeError("invalid digest startup succeeded")
                        event.update(
                            startup_rejected=True,
                            exit_code=process.returncode,
                            startup_seconds=time.perf_counter() - started,
                        )
                    else:
                        io.ready(process, url, digest)
                        event["startup_seconds"] = time.perf_counter() - started
                        first = io.request(url + "/predict", {"text": "  TRIANGLE  "})
                        event["first_request"] = first
                        if first["outcome"] != "ok" or first["payload"]["bundle_sha256"] != digest:
                            raise RuntimeError("first inference failed/identity differs")
                        batch_started = time.perf_counter()
                        rows = io.load(
                            url + "/predict",
                            {"text": "  TRIANGLE  "},
                            count=requests,
                            concurrency=concurrency,
                        )
                        event["load_seconds"] = time.perf_counter() - batch_started
                        event["warm_requests"] = rows
                        event["summary"] = summarize(rows)
                        event["fault_probes"] = [
                            io.request(url + "/predict", {"text": " "}),
                            io.request(url + "/predict", {"text": "triangle"}, timeout=1e-9),
                        ]
                        event["fault_summary"] = summarize(event["fault_probes"])
                        if any(
                            row["outcome"] != "ok" or row["payload"] != first["payload"]
                            for row in rows
                        ):
                            raise RuntimeError("warm inference failed or differs")
                if stage == "rejected":
                    log_text = log_path.read_text(encoding="utf-8")
                    if "manifest verification failed" not in log_text or "sha256" not in log_text:
                        raise RuntimeError("startup failed for a reason other than bad digest")
                    event["rejection_reason"] = "manifest_digest_mismatch"
                event["stage_status"] = "COMPLETE"
            except BaseException as exc:
                event.update(stage_status="FAILED", failure_reason=f"{type(exc).__name__}: {exc}")
                raise
            finally:
                event.setdefault("startup_seconds", time.perf_counter() - started)
                event["cleanup_exit_code"] = process.returncode if process is not None else None
                if log_path.is_file():
                    event["startup_log"] = {"path": log_path.name, "sha256": file_sha256(log_path)}
                _save_report(output, report)
        baseline = events[0]["first_request"]["payload"]
        if (
            baseline["predicted_label"] != "circle"
            or events[2]["first_request"]["payload"]["predicted_label"] != "triangle"
        ):
            raise RuntimeError("A/B saved-model behavior did not differ")
        for index in (1, 4):
            if events[index]["first_request"]["payload"] != baseline:
                raise RuntimeError("restart/rollback identity or prediction differs")
    except BaseException as exc:
        report.update(run_status="FAILED", failure_reason=f"{type(exc).__name__}: {exc}")
        _save_report(output, report)
        raise
    report["run_status"] = "COMPLETE"
    _save_report(output, report)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--requests", type=int, default=12)
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()
    print(run_demo(args.output, requests=args.requests, concurrency=args.concurrency))
