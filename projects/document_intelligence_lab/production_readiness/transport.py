"""Shared low-level local transport, not the learner lifecycle orchestration."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Any, Protocol

from ..artifacts import json_bytes
from ..service.app import create_app


def factory() -> Any:
    """Private child factory reuses the existing app and shared preprocessing.

    Trust is scoped to bundles generated locally by this operator harness; never
    accept a bundle path/digest/pickle trust decision in a prediction request.
    """
    return create_app(
        Path(os.environ["ROADMAP_LIFECYCLE_BUNDLE"]),
        os.environ["ROADMAP_LIFECYCLE_DIGEST"],
        trusted_local_artifact=True,
    )


def request(
    url: str, payload: dict[str, Any] | None = None, *, timeout: float = 2.0
) -> dict[str, Any]:
    started = time.perf_counter()
    row: dict[str, Any] = {"status": None, "payload": None, "outcome": "transport_error"}
    body = None if payload is None else json_bytes(payload)
    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        # Ignore proxy environment variables for these explicitly local requests.
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
            req, timeout=timeout
        ) as response:
            row.update(status=response.status, payload=json.load(response), outcome="ok")
    except urllib.error.HTTPError as exc:
        row.update(status=exc.code, outcome="http_error")
    except TimeoutError:
        row["outcome"] = "timeout"
    except urllib.error.URLError as exc:
        row["outcome"] = "timeout" if isinstance(exc.reason, TimeoutError) else "transport_error"
    except (OSError, json.JSONDecodeError) as exc:
        row["error_type"] = type(exc).__name__
    row["seconds"] = time.perf_counter() - started
    return row


@contextmanager
def child(
    bundle: Path, digest: str, log_path: Path
) -> Iterator[tuple[subprocess.Popen[bytes], str]]:
    # Reserve then release an ephemeral loopback port. A bind race is possible;
    # readiness must fail rather than silently accepting the wrong bundle/process.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = {
        **os.environ,
        "ROADMAP_LIFECYCLE_BUNDLE": str(bundle.resolve()),
        "ROADMAP_LIFECYCLE_DIGEST": digest,
        "OMP_NUM_THREADS": "1",
    }
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "projects.document_intelligence_lab.production_readiness.transport:factory",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--workers",
                "1",
                "--no-access-log",
            ],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            yield process, f"http://127.0.0.1:{port}"
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def wait_ready(
    process: ChildProcess, url: str, digest: str, *, deadline_seconds: float = 20
) -> dict[str, Any]:
    started = time.perf_counter()
    while time.perf_counter() - started < deadline_seconds:
        if process.poll() is not None:
            raise RuntimeError(f"child exited before readiness: {process.returncode}")
        result = request(url + "/ready", timeout=0.2)
        if result["outcome"] == "ok":
            if result["payload"] != {"ready": True, "bundle_sha256": digest}:
                raise RuntimeError("readiness identity mismatch")
            return result
        time.sleep(0.025)
    raise TimeoutError("service startup deadline exceeded")


class ChildProcess(Protocol):
    pid: int
    returncode: int | None

    def wait(self, timeout: float | None = None) -> int: ...

    def poll(self) -> int | None: ...


class LifecycleTransport(Protocol):
    """Injectable I/O seam; the learner still implements every lifecycle decision."""

    def child(
        self, bundle: Path, digest: str, log_path: Path
    ) -> AbstractContextManager[tuple[ChildProcess, str]]: ...

    def ready(self, process: ChildProcess, url: str, digest: str) -> dict[str, Any]: ...

    def request(
        self, url: str, payload: dict[str, Any] | None = None, *, timeout: float = 2.0
    ) -> dict[str, Any]: ...

    def load(
        self, url: str, payload: dict[str, Any], *, count: int, concurrency: int
    ) -> list[dict[str, Any]]: ...


class LocalTransport:
    """Actual subprocess/TCP adapter, intentionally without an A/B orchestration."""

    child = staticmethod(child)
    ready = staticmethod(wait_ready)
    request = staticmethod(request)

    def load(
        self, url: str, payload: dict[str, Any], *, count: int, concurrency: int
    ) -> list[dict[str, Any]]:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            return list(pool.map(lambda _: request(url, payload), range(count)))
