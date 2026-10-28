"""Offline transport contracts; these are synthetic, never vLLM measurements."""

import asyncio
import gzip
import importlib
import json
from collections.abc import AsyncIterator
from types import ModuleType

import httpx
import pytest

serving = "labs.05_model_serving.demo_client"


# Initialize Windows' event-loop wakeup socket before the function-scoped
# offline guard. The guard remains active for every test and every HTTP request.
@pytest.fixture(scope="module", autouse=True)
def initialized_runner(request: pytest.FixtureRequest) -> None:
    request.getfixturevalue("_module_scoped_runner")


def api() -> ModuleType:
    return importlib.import_module(serving)


def event(payload: object) -> bytes:
    return b"data: " + json.dumps(payload, ensure_ascii=False).encode() + b"\n\n"


def chunk(text: str | None = None, **delta: object) -> bytes:
    if text is not None:
        delta["content"] = text
    return event({"model": "local-qwen", "choices": [{"index": 0, "delta": delta}]})


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


class Stream(httpx.AsyncByteStream):
    def __init__(self, parts: list[bytes], clock: Clock | None = None) -> None:
        self.parts, self.clock, self.closed = parts, clock, False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for index, part in enumerate(self.parts, 1):
            if self.clock:
                self.clock.now = index / 10
            yield part

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio(loop_scope="module")
async def test_split_utf8_records_metadata_and_server_usage() -> None:
    clock = Clock()
    first = chunk("Привет")
    split_at = first.index("П".encode()) + 1  # Split inside one UTF-8 codepoint.
    stream = Stream(
        [
            chunk(role="assistant"),
            first[:split_at],
            first[split_at:],
            chunk("!"),
            event({"choices": [], "usage": {"prompt_tokens": 9, "completion_tokens": 3}}),
            b"data: [DONE]\n\n",
        ],
        clock,
    )
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await api().stream_chat(
            client, "http://127.0.0.1:8000/v1", "local-qwen", "Say hello", clock=clock
        )
    assert result.status == "ok"
    assert result.text == "Привет!"
    assert result.ttft_ms == pytest.approx(300)
    assert result.e2e_ms == pytest.approx(600)
    assert result.content_offsets_ms == pytest.approx((300, 400))
    assert result.content_deltas_ms == pytest.approx((100,))
    assert (result.prompt_tokens, result.completion_tokens) == (9, 3)
    assert stream.closed
    assert len(requests) == 1
    payload = json.loads(requests[0].content)
    assert payload["model"] == "local-qwen"
    assert payload["max_tokens"] == 128
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert "tools" not in payload


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.com/v1",
        "http://0.0.0.0:8000/v1",
        "http://127.0.0.1.evil.test/v1",
        "http://user:secret@127.0.0.1/v1",
        "http://127.0.0.1/v1?key=secret",
        "http://127.0.0.1/v1#secret",
    ],
)
def test_reject_endpoint_before_network(endpoint: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        api().loopback_base(endpoint)


@pytest.mark.parametrize(
    ("endpoint", "want"),
    [
        ("http://localhost:8000/v1/", "http://127.0.0.1:8000/v1"),
        ("http://[::1]:8000/v1", "http://[::1]:8000/v1"),
    ],
)
def test_loopback_normalization(endpoint: str, want: str) -> None:
    assert api().loopback_base(endpoint) == want


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(
    ("parts", "error"),
    [
        ([b"data: nope\n\n"], "protocol"),
        ([event({"error": {"message": "secret"}})], "provider"),
        ([chunk("partial")], "protocol"),
        ([event({"choices": [{"delta": {"content": 4}}]})], "protocol"),
        ([event({"choices": [], "usage": {"completion_tokens": True}})], "protocol"),
        ([b"data: \xff\n\n"], "protocol"),
        ([b"data: " + b"x" * 70000], "limit"),
        ([chunk("partial"), event({"error": {"message": "secret"}})], "provider"),
    ],
)
async def test_malformed_or_provider_error_closes_without_replay(
    parts: list[bytes], error: str
) -> None:
    stream = Stream(parts)
    attempts = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await api().stream_chat(client, "http://127.0.0.1:8000/v1", "local-qwen", "Hello")
    assert result.status == "error"
    assert result.error == error
    assert "secret" not in repr(result)
    assert attempts == 1
    assert stream.closed


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(
    ("status", "content_type", "error"),
    [
        (503, "application/json", "http_503"),
        (302, "text/event-stream", "http_302"),
        (200, "application/json", "protocol"),
    ],
)
async def test_http_errors_never_follow_redirects_or_replay(
    status: int, content_type: str, error: str
) -> None:
    attempts = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            status,
            headers={"content-type": content_type, "location": "https://example.com/"},
            content=b"secret",
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handle), follow_redirects=True
    ) as client:
        result = await api().stream_chat(client, "http://127.0.0.1/v1", "local-qwen", "Hello")
    assert result.error == error
    assert attempts == 1


class BlockingStream(httpx.AsyncByteStream):
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        self.started.set()
        yield chunk("partial")
        await asyncio.Event().wait()

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio(loop_scope="module")
async def test_total_deadline_after_content_closes_stream() -> None:
    stream = BlockingStream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=stream
            )
        )
    ) as client:
        result = await api().stream_chat(
            client,
            "http://127.0.0.1/v1",
            "local-qwen",
            "Hello",
            config=api().ClientConfig(deadline_s=0.02),
        )
    assert result.status == "deadline"
    assert result.text == "partial"
    assert result.ttft_ms is not None
    assert result.e2e_ms < 500
    assert stream.closed


@pytest.mark.asyncio(loop_scope="module")
async def test_caller_cancellation_propagates_and_closes_stream() -> None:
    stream = BlockingStream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=stream
            )
        )
    ) as client:
        task = asyncio.create_task(
            api().stream_chat(client, "http://127.0.0.1/v1", "local-qwen", "Hi")
        )
        await stream.started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert stream.closed


@pytest.mark.asyncio(loop_scope="module")
async def test_connection_error_has_one_attempt_and_sanitized_error() -> None:
    attempts = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("secret", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await api().stream_chat(client, "http://127.0.0.1/v1", "local-qwen", "Hi")
    assert result.error == "transport"
    assert attempts == 1
    assert result.ttft_ms is None


@pytest.mark.asyncio(loop_scope="module")
async def test_midstream_transport_failure_keeps_partial_and_never_replays() -> None:
    class BrokenStream(Stream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield chunk("partial")
            raise httpx.ReadError("private server error")

    stream = BrokenStream([])
    attempts = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await api().stream_chat(client, "http://127.0.0.1/v1", "local-qwen", "Hi")
    assert result.text == "partial"
    assert result.status == "error"
    assert result.error == "transport"
    assert result.ttft_ms is not None
    assert stream.closed
    assert attempts == 1


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("has_partial", [False, True])
async def test_malformed_gzip_returns_sanitized_result_and_preserves_partial(
    has_partial: bool,
) -> None:
    clock = Clock()
    encoded = gzip.compress(chunk("partial"))
    # Corrupt the CRC/footer after the decoder has already yielded valid content.
    parts = [encoded[:-8], b"\xff" * 8] if has_partial else [b"not a gzip body"]
    stream = Stream(parts, clock)
    attempts = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream", "content-encoding": "gzip"},
            stream=stream,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await api().stream_chat(
            client, "http://127.0.0.1/v1", "local-qwen", "Hi", clock=clock
        )
    assert result.status == "error"
    assert result.error == "protocol"
    assert result.text == ("partial" if has_partial else "")
    assert result.ttft_ms == (100.0 if has_partial else None)
    assert result.e2e_ms == (200.0 if has_partial else 100.0)
    assert stream.closed
    assert attempts == 1


@pytest.mark.asyncio(loop_scope="module")
async def test_live_smoke_retains_malformed_gzip_as_raw_error_record() -> None:
    smoke = importlib.import_module("labs.05_model_serving.smoke.endpoint")
    methods: list[str] = []
    stream = Stream([b"not a gzip body"])

    def handle(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "local-qwen"}]})
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream", "content-encoding": "gzip"},
            stream=stream,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        report = await smoke.collect(
            client,
            "http://127.0.0.1/v1",
            "local-qwen",
            requests=1,
            concurrency=1,
            state="cold",
            metadata={},
        )
    assert report["raw"][0]["status"] == "error"
    assert report["raw"][0]["error"] == "protocol"
    assert report["summary"]["completed"] == 0
    assert report["summary"]["errors"] == 1
    assert methods == ["GET", "POST"]
    assert stream.closed


@pytest.mark.asyncio(loop_scope="module")
async def test_whole_response_budget_bounds_many_small_records() -> None:
    stream = Stream([chunk("a")] * 20 + [b"data: [DONE]\n\n"])
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=stream
            )
        )
    ) as client:
        result = await api().stream_chat(
            client,
            "http://127.0.0.1/v1",
            "local-qwen",
            "Hi",
            config=api().ClientConfig(max_response_bytes=300),
        )
    assert result.error == "limit"
    assert 0 < len(result.text) < 20
    assert stream.closed


@pytest.mark.asyncio(loop_scope="module")
async def test_bounded_batch_limits_active_calls_and_queue_deadline() -> None:
    active = peak = 0

    class SlowStream(Stream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.03)
            yield chunk("ok")
            yield b"data: [DONE]\n\n"

        async def aclose(self) -> None:
            nonlocal active
            active -= 1
            await super().aclose()

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=SlowStream([])
            )
        )
    ) as client:
        results = await api().bounded_batch(
            client, "http://127.0.0.1/v1", "local-qwen", ["a"] * 4, concurrency=2
        )
        with pytest.raises(ValueError, match="batch"):
            await api().bounded_batch(client, "http://127.0.0.1/v1", "local-qwen", ["a"] * 9)
        expired = await api().bounded_batch(
            client,
            "http://127.0.0.1/v1",
            "local-qwen",
            ["a"] * 3,
            concurrency=1,
            config=api().ClientConfig(deadline_s=0.045),
        )
    assert peak == 2
    assert [r.result.text for r in results] == ["ok"] * 4
    assert results[2].queue_ms >= 5
    assert expired[-1].result.status == "deadline"
    assert expired[-1].result.ttft_ms is None


@pytest.mark.asyncio(loop_scope="module")
async def test_sse_multiline_comment_crlf_and_missing_usage() -> None:
    stream = Stream(
        [
            b': heartbeat\r\nid: 1\r\ndata: {"choices":\r\ndata: []}\r\n\r\n',
            chunk("ok"),
            b"data: [DONE]\n\n",
        ]
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=stream
            )
        )
    ) as client:
        result = await api().stream_chat(client, "http://127.0.0.1/v1", "local-qwen", "Hi")
    assert result.text == "ok"
    assert result.completion_tokens is None


@pytest.mark.asyncio(loop_scope="module")
async def test_live_smoke_readiness_requires_model_and_saves_derived_raw_report() -> None:
    smoke = importlib.import_module("labs.05_model_serving.smoke.endpoint")
    methods: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "local-qwen"}]})
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=Stream([chunk("ok"), b"data: [DONE]\n\n"]),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match="model"):
            await smoke.collect(
                client,
                "http://127.0.0.1/v1",
                "wrong",
                requests=1,
                concurrency=1,
                state="cold",
                metadata={},
            )
        report = await smoke.collect(
            client,
            "http://127.0.0.1/v1",
            "local-qwen",
            requests=2,
            concurrency=1,
            state="warm",
            metadata={"engine": "vllm"},
        )
    assert methods == ["GET", "GET", "POST", "POST"]
    assert report["schema_version"] == 1
    assert report["evidence"] == "live_endpoint"
    assert report["summary"]["completed"] == 2
    assert report["summary"]["completed_output_tokens_per_s"] is None
    assert report["memory_bytes"] is None
    assert report["state"] == "warm"
    assert "text" not in report["raw"][0]


@pytest.mark.asyncio(loop_scope="module")
async def test_readiness_stops_before_retaining_oversize_body_and_never_chats() -> None:
    smoke = importlib.import_module("labs.05_model_serving.smoke.endpoint")
    methods: list[str] = []

    class LargeStream(Stream):
        reads = 0

        async def __aiter__(self) -> AsyncIterator[bytes]:
            for _ in range(4):
                self.reads += 1
                yield b"x" * 1048576

    stream = LargeStream([])

    def handle(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        return httpx.Response(200, stream=stream)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match="readiness"):
            await smoke.collect(
                client,
                "http://127.0.0.1/v1",
                "local-qwen",
                requests=1,
                concurrency=1,
                state="cold",
                metadata={},
            )
    assert stream.reads == 2
    assert stream.closed
    assert methods == ["GET"]


@pytest.mark.asyncio(loop_scope="module")
async def test_readiness_rejects_compression_before_decoding_or_reading_body() -> None:
    smoke = importlib.import_module("labs.05_model_serving.smoke.endpoint")

    class CompressedStream(Stream):
        reads = 0

        async def __aiter__(self) -> AsyncIterator[bytes]:
            self.reads += 1
            yield gzip.compress(b"x" * 2097152)

    stream = CompressedStream([])
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, headers={"content-encoding": "gzip"}, stream=stream)
        )
    ) as client:
        with pytest.raises(ValueError, match="readiness"):
            await smoke.collect(
                client,
                "http://127.0.0.1/v1",
                "local-qwen",
                requests=1,
                concurrency=1,
                state="cold",
                metadata={},
            )
    assert stream.reads == 0
    assert stream.closed


@pytest.mark.asyncio(loop_scope="module")
async def test_batch_validates_every_prompt_before_dispatch() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match="prompt"):
            await api().bounded_batch(client, "http://127.0.0.1/v1", "local-qwen", ["ok", " "])
    assert requests == []


def test_smoke_requires_explicit_live_flag_without_touching_endpoint() -> None:
    smoke = importlib.import_module("labs.05_model_serving.smoke.endpoint")
    assert smoke.main([]) == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"deadline_s": 0},
        {"deadline_s": float("nan")},
        {"max_tokens": 129},
        {"max_tokens": True},
        {"max_response_bytes": 0},
    ],
)
def test_invalid_request_config_fails_before_network(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="must"):
        api().ClientConfig(**kwargs)
