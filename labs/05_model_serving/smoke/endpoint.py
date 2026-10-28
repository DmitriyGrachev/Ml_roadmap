"""Explicit operator-triggered loopback endpoint smoke; never run by pytest."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import re
import time
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from types import ModuleType


def _module(name: str) -> ModuleType:
    return importlib.import_module("labs.05_model_serving." + name)


async def collect(
    client: httpx.AsyncClient,
    endpoint: str,
    model: str,
    *,
    requests: int,
    concurrency: int,
    state: str,
    metadata: dict[str, object],
) -> dict[str, object]:
    """Validate readiness then collect finite raw records; endpoint provenance is external."""
    api = _module("demo_client")
    base = api.loopback_base(endpoint)
    if type(requests) is not int or not 1 <= requests <= 8 or concurrency not in (1, 2):
        raise ValueError("requests must be 1..8; concurrency 1 or 2")
    if state not in ("cold", "warm"):
        raise ValueError("state must be cold or warm")
    async with asyncio.timeout(10):
        async with client.stream(
            "GET",
            base + "/models",
            timeout=10,
            follow_redirects=False,
            headers={"Accept-Encoding": "identity"},
        ) as readiness:
            # Refuse compressed readiness before decoding: a small wire chunk can
            # expand beyond the budget inside the HTTP decoder before yielding.
            if readiness.status_code != 200 or readiness.headers.get(
                "content-encoding", "identity"
            ).strip().lower() not in ("", "identity"):
                raise ValueError("readiness failed: status or unsupported compression")
            body = bytearray()
            async for part in readiness.aiter_bytes():
                if len(part) > 1048576 - len(body):
                    raise ValueError("readiness failed: body size limit")
                body.extend(part)
            try:
                available = json.loads(body)["data"]
                if not isinstance(available, list) or not any(
                    isinstance(item, dict) and item.get("id") == model for item in available
                ):
                    raise ValueError("model id absent from readiness")
            except (ValueError, TypeError, KeyError):
                raise ValueError("model id absent from readiness") from None
    start = time.perf_counter()  # Monotonic, high resolution; no invented epsilon duration.
    results = await api.bounded_batch(
        client,
        base,
        model,
        ["Answer in one short sentence: what is a queue?"] * requests,
        concurrency=concurrency,
    )
    elapsed_s = time.perf_counter() - start
    raw: list[dict[str, object]] = []
    for index, queued in enumerate(results):
        record = asdict(queued.result)
        record.pop("text")  # Do not log generated content or prompts by default.
        record.update(
            {
                "request_index": index,
                "queue_ms": queued.queue_ms,
                "content_deltas_ms": queued.result.content_deltas_ms,
            }
        )
        raw.append(record)
    return {
        "schema_version": 1,
        "evidence": "live_endpoint",
        "model_server_id": model,
        "runtime_and_model": metadata,
        "state": state,
        "concurrency": concurrency,
        "request_config": {
            "max_tokens": 128,
            "enable_thinking": False,
            "temperature": 0.7,
            "deadline_s": 30,
            "max_requests": 8,
            "attempts_per_request": 1,
        },
        "units": {
            "times": "ms",
            "run_elapsed": "s",
            "memory": "bytes",
            "tokens": "server usage, not chunks",
        },
        "memory_bytes": None,
        "run_elapsed_s": elapsed_s,
        "raw": raw,
        "summary": _module("experiments.report").summarize(
            raw, elapsed_s=elapsed_s, evidence="live_endpoint"
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--endpoint")
    parser.add_argument("--model")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--state", choices=("cold", "warm"), default="cold")
    parser.add_argument("--requests", type=int, default=1)
    parser.add_argument("--concurrency", type=int, choices=(1, 2), default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.live:
        print("NOT_RUN: provide --live and prepared loopback endpoint/model/manifest explicitly")
        return 2
    try:
        if not args.endpoint or not args.model or not args.manifest or not args.output:
            raise ValueError("endpoint, model, manifest and new output path required")
        _module("demo_client").loopback_base(args.endpoint)
        metadata = json.loads(args.manifest.read_text(encoding="utf-8"))
        if (
            not isinstance(metadata, dict)
            or metadata.get("server_model_id") != args.model
            or re.fullmatch(r"[0-9a-f]{40}", str(metadata.get("model_revision"))) is None
            or not isinstance(metadata.get("runtime_versions"), dict)
        ):
            raise ValueError("prepared model/runtime metadata required")
        if args.output.exists() or not args.output.parent.is_dir():
            raise ValueError("output must be a new file in an existing directory")

        async def run() -> dict[str, object]:
            async with httpx.AsyncClient(trust_env=False, follow_redirects=False) as client:
                return await collect(
                    client,
                    args.endpoint,
                    args.model,
                    requests=args.requests,
                    concurrency=args.concurrency,
                    state=args.state,
                    metadata=metadata,
                )

        report = asyncio.run(run())
        with args.output.open("x", encoding="utf-8") as destination:
            json.dump(report, destination, ensure_ascii=False, indent=2, allow_nan=False)
        print(
            "SAVED: live_endpoint report; vLLM provenance and GPU evidence require operator review"
        )
        return 0 if report["summary"]["errors"] == 0 else 1  # type: ignore[index]
    except (ValueError, OSError, httpx.HTTPError, TimeoutError):
        print("FAILED: input/readiness/connection/output check; no automatic replay")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
