"""Teacher SSE client. No networking until an explicitly awaited request.

One attempt, zero automatic retries: a partial generation is never replayed.
Transport injection is for offline contract tests, not performance evidence.
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import math
import time
from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass, replace
from urllib.parse import urlsplit, urlunsplit

import httpx


@dataclass(frozen=True)
class ClientConfig:
    deadline_s: float = 30.0
    max_tokens: int = 128
    max_event_bytes: int = 65536
    max_response_bytes: int = 1048576

    def __post_init__(self) -> None:
        if (
            type(self.deadline_s) not in (int, float)
            or not math.isfinite(self.deadline_s)
            or not 0 < self.deadline_s <= 120
        ):
            raise ValueError("deadline_s must be finite and in (0, 120]")
        if type(self.max_tokens) is not int or not 1 <= self.max_tokens <= 128:
            raise ValueError("max_tokens must be an integer in [1, 128]")
        for value in (self.max_event_bytes, self.max_response_bytes):
            if type(value) is not int or not 1 <= value <= 1048576:
                raise ValueError("byte limits must be integers in [1, 1048576]")


@dataclass(frozen=True)
class StreamResult:
    status: str
    text: str
    error: str | None
    ttft_ms: float | None
    e2e_ms: float
    content_offsets_ms: tuple[float, ...]
    prompt_tokens: int | None
    completion_tokens: int | None
    finish_reason: str | None

    @property
    def content_deltas_ms(self) -> tuple[float, ...]:
        return tuple(
            b - a
            for a, b in zip(self.content_offsets_ms, self.content_offsets_ms[1:], strict=False)
        )


@dataclass(frozen=True)
class QueuedResult:
    queue_ms: float
    result: StreamResult


class StreamFailure(Exception):
    """Only a fixed error category; never a server body, URL or credential."""


DEFAULT_CONFIG = ClientConfig()


def loopback_base(endpoint: str) -> str:
    """Accept only explicit HTTP loopback /v1, without auth or redirects."""
    try:
        parsed = urlsplit(endpoint)
        host = parsed.hostname
        port = parsed.port
        if host == "localhost":
            host = "127.0.0.1"  # Avoid DNS lookup, including modified localhost resolution.
        if (
            parsed.scheme != "http"
            or host is None
            or not ipaddress.ip_address(host).is_loopback
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") != "/v1"
        ):
            raise ValueError
        authority = f"[{host}]" if ":" in host else host
        if port is not None:
            authority += f":{port}"
        return urlunsplit(("http", authority, "/v1", "", ""))
    except ValueError:
        raise ValueError("endpoint must be an HTTP loopback /v1 URL without credentials") from None


async def sse_records(response: httpx.Response, config: ClientConfig) -> AsyncIterator[str]:
    """Frame SSE bytes before UTF-8 decoding; bound lines, records and whole body."""
    pending = b""
    data: list[bytes] = []
    total = record_size = 0
    async for part in response.aiter_bytes():
        total += len(part)
        if total > config.max_response_bytes:
            raise StreamFailure("limit")
        pending += part
        while b"\n" in pending:
            line, pending = pending.split(b"\n", 1)
            line = line.removesuffix(b"\r")
            record_size += len(line) + 1
            if record_size > config.max_event_bytes:
                raise StreamFailure("limit")
            if not line:
                if data:
                    try:
                        yield b"\n".join(data).decode("utf-8", errors="strict")
                    except UnicodeDecodeError:
                        raise StreamFailure("protocol") from None
                data = []
                record_size = 0
            elif line.startswith(b"data:"):
                data.append(line[5:].removeprefix(b" "))
        if len(pending) + record_size > config.max_event_bytes:
            raise StreamFailure("limit")
    if pending or data:
        raise StreamFailure("protocol")


def _token_count(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise StreamFailure("protocol")
    return value


def _validate_request(model: str, prompt: str) -> None:
    if not model or model != model.strip() or len(model) > 200:
        raise ValueError("explicit model server id required")
    if not prompt.strip() or len(prompt.encode("utf-8")) > 8192:
        raise ValueError("prompt must contain 1..8192 UTF-8 bytes")


async def stream_chat(
    client: httpx.AsyncClient,
    endpoint: str,
    model: str,
    prompt: str,
    *,
    config: ClientConfig = DEFAULT_CONFIG,
    clock: Callable[[], float] = time.monotonic,
) -> StreamResult:
    """Measure first nonempty answer content, never role/reasoning/usage metadata.

    Caller cancellation propagates after stream closure. Deadline and protocol/
    transport failures return partial content with an explicit non-success status.
    Tokens are exclusively server usage counts; chunks are not token counts.
    """
    base = loopback_base(endpoint)
    _validate_request(model, prompt)
    start = clock()
    content: list[str] = []
    offsets: list[float] = []
    input_tokens = output_tokens = None
    finish_reason = error = None
    status = "ok"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": config.max_tokens,
        "temperature": 0.7,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        async with asyncio.timeout(config.deadline_s):
            async with client.stream(
                "POST",
                base + "/chat/completions",
                json=body,
                timeout=config.deadline_s,
                follow_redirects=False,
            ) as response:
                if response.status_code != 200:
                    raise StreamFailure(f"http_{response.status_code}")
                if response.headers.get("content-type", "").split(";")[0] != "text/event-stream":
                    raise StreamFailure("protocol")
                done = False
                async for record in sse_records(response, config):
                    if record == "[DONE]":
                        done = True
                        break
                    try:
                        payload = json.loads(record)
                    except ValueError:
                        raise StreamFailure("protocol") from None
                    if not isinstance(payload, dict):
                        raise StreamFailure("protocol")
                    if "error" in payload:
                        raise StreamFailure("provider")
                    if payload.get("model", model) != model:
                        raise StreamFailure("protocol")
                    usage = payload.get("usage")
                    if usage is not None:
                        if not isinstance(usage, dict):
                            raise StreamFailure("protocol")
                        input_tokens = _token_count(usage.get("prompt_tokens"))
                        output_tokens = _token_count(usage.get("completion_tokens"))
                    choices = payload.get("choices")
                    if not isinstance(choices, list) or len(choices) > 1:
                        raise StreamFailure("protocol")
                    if not choices:
                        continue
                    choice = choices[0]
                    if not isinstance(choice, dict) or not isinstance(choice.get("delta"), dict):
                        raise StreamFailure("protocol")
                    delta = choice["delta"]
                    if delta.get("tool_calls"):
                        raise StreamFailure("protocol")
                    text = delta.get("content")
                    if text is not None and not isinstance(text, str):
                        raise StreamFailure("protocol")
                    if text:
                        content.append(text)
                        offsets.append((clock() - start) * 1000)
                    reason = choice.get("finish_reason")
                    if reason is not None:
                        if not isinstance(reason, str):
                            raise StreamFailure("protocol")
                        finish_reason = reason
                if not done:
                    raise StreamFailure("protocol")
    except (TimeoutError, httpx.TimeoutException):
        status, error = "deadline", "deadline"
    except httpx.TransportError:
        status, error = "error", "transport"
    except httpx.DecodingError:
        status, error = "error", "protocol"
    except StreamFailure as exc:
        status, error = "error", str(exc)
    return StreamResult(
        status,
        "".join(content),
        error,
        offsets[0] if offsets else None,
        (clock() - start) * 1000,
        tuple(offsets),
        input_tokens,
        output_tokens,
        finish_reason,
    )


async def bounded_batch(
    client: httpx.AsyncClient,
    endpoint: str,
    model: str,
    prompts: Sequence[str],
    *,
    concurrency: int = 1,
    config: ClientConfig = DEFAULT_CONFIG,
) -> tuple[QueuedResult, ...]:
    """Finite batch (1..8), active requests (1..2), deadline includes local queue."""
    if type(concurrency) is not int or concurrency not in (1, 2) or not 1 <= len(prompts) <= 8:
        raise ValueError("batch requires 1..8 requests and concurrency 1 or 2")
    loopback_base(endpoint)
    for prompt in prompts:
        _validate_request(model, prompt)
    semaphore = asyncio.Semaphore(concurrency)

    async def one(prompt: str) -> QueuedResult:
        queued = time.monotonic()
        try:
            async with asyncio.timeout(config.deadline_s):
                await semaphore.acquire()
        except TimeoutError:
            elapsed = (time.monotonic() - queued) * 1000
            return QueuedResult(
                elapsed,
                StreamResult("deadline", "", "deadline", None, 0.0, (), None, None, None),
            )
        try:
            queue_ms = (time.monotonic() - queued) * 1000
            remaining = config.deadline_s - queue_ms / 1000
            if remaining <= 0:
                return QueuedResult(
                    queue_ms,
                    StreamResult("deadline", "", "deadline", None, 0.0, (), None, None, None),
                )
            result = await stream_chat(
                client, endpoint, model, prompt, config=replace(config, deadline_s=remaining)
            )
            return QueuedResult(queue_ms, result)
        finally:
            semaphore.release()

    return tuple(await asyncio.gather(*(one(prompt) for prompt in prompts)))
