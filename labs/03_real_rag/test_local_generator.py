"""Offline adapter contracts; real model quality is a separate experiment."""

import json
from dataclasses import replace
from importlib import import_module
from typing import Any

import httpx
import pytest

demo = import_module("labs.03_real_rag.demo")


def adapter() -> Any:
    return import_module("labs.03_real_rag.local_generator")


@pytest.fixture(scope="module", autouse=True)
def initialized_runner(request: pytest.FixtureRequest) -> None:
    request.getfixturevalue("_module_scoped_runner")


def response(text: str, finish: str = "stop", done: bool = True) -> httpx.Response:
    records = [
        {"choices": [{"index": 0, "delta": {"content": text}}]},
        {"choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
        {"choices": [], "usage": {"prompt_tokens": 30, "completion_tokens": 20}},
    ]
    body = b"".join(b"data: " + json.dumps(r).encode() + b"\n\n" for r in records)
    if done:
        body += b"data: [DONE]\n\n"
    return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})


def passages() -> tuple[Any, ...]:
    rag = import_module("modules.06_rag.walkthrough")
    return tuple(rag.chunks(demo.teacher_sources()[0])[:1])


@pytest.mark.asyncio(loop_scope="module")
async def test_valid_json_uses_real_bounded_client_and_public_context() -> None:
    requests: list[httpx.Request] = []

    def serve(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response('{"text":"Use 300 dpi.","citation_ids":["A-SCAN@1:p1"]}')

    generator = adapter().LocalGenerator(transport=httpx.MockTransport(serve))
    draft = await generator.generate("scanner settings", passages())
    assert draft == demo.Draft("Use 300 dpi.", ("A-SCAN@1:p1",))
    assert len(requests) == 1
    assert str(requests[0].url) == "http://127.0.0.1:11434/v1/chat/completions"
    body = json.loads(requests[0].content)
    assert body["max_tokens"] == 128
    assert "300 dpi" in body["messages"][0]["content"]
    assert "STAFF-ONLY" not in body["messages"][0]["content"]
    assert generator.last_result.completion_tokens == 20


@pytest.mark.parametrize(
    "text",
    [
        "not JSON",
        '{"text":" ","citation_ids":["A-SCAN@1:p1"]}',
        '{"text":"x","citation_ids":[]}',
        '{"text":"x","citation_ids":["A-STAFF@1:p1"]}',
        '{"text":"x","citation_ids":["A-SCAN@1:p1","A-SCAN@1:p1"]}',
        '{"text":"x","text":"y","citation_ids":["A-SCAN@1:p1"]}',
    ],
)
@pytest.mark.asyncio(loop_scope="module")
async def test_invalid_generation_is_rejected(text: str) -> None:
    generator = adapter().LocalGenerator(transport=httpx.MockTransport(lambda _: response(text)))
    with pytest.raises(adapter().InvalidGeneration):
        await generator.generate("scanner settings", passages())


@pytest.mark.parametrize(("finish", "done"), [("length", True), ("stop", False)])
@pytest.mark.asyncio(loop_scope="module")
async def test_partial_or_truncated_output_never_becomes_draft(finish: str, done: bool) -> None:
    text = '{"text":"300 dpi","citation_ids":["A-SCAN@1:p1"]}'
    generator = adapter().LocalGenerator(
        transport=httpx.MockTransport(lambda _: response(text, finish, done))
    )
    with pytest.raises(demo.ProviderUnavailable):
        await generator.generate("scanner settings", passages())


@pytest.mark.asyncio(loop_scope="module")
async def test_provider_timeout_has_no_retry() -> None:
    count = 0

    def fail(request: httpx.Request) -> httpx.Response:
        nonlocal count
        count += 1
        raise httpx.ReadTimeout("timeout", request=request)

    generator = adapter().LocalGenerator(transport=httpx.MockTransport(fail))
    with pytest.raises(demo.ProviderUnavailable):
        await generator.generate("scanner settings", passages())
    assert count == 1


def test_no_evidence_or_revoked_context_never_calls_provider() -> None:
    def fail(_: httpx.Request) -> httpx.Response:
        pytest.fail("context must be checked before network")

    generator = adapter().LocalGenerator(transport=httpx.MockTransport(fail))
    sources = demo.teacher_sources()
    assert (
        demo.answer_query("volcano insurance", sources, generator=generator).status == "no_answer"
    )
    current = (replace(sources[0], access="staff"), *sources[1:])
    result = demo.answer_query(
        "scanner settings", sources, current_sources=current, generator=generator, k=1
    )
    assert result.status == "no_answer"
    assert generator.last_result is None


@pytest.mark.asyncio(loop_scope="module")
async def test_sync_adapter_rejects_active_loop_without_coroutine_leak() -> None:
    generator = adapter().LocalGenerator()
    with pytest.raises(RuntimeError, match="event loop"):
        generator("scanner", passages())


def test_public_endpoint_rejected_before_network() -> None:
    with pytest.raises(ValueError, match="loopback"):
        adapter().LocalGenerator(endpoint="https://example.com/v1")


def test_runtime_identity_uses_verified_nested_manifest_digest() -> None:
    digest = "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"
    model = {"name": "qwen2.5:latest", "digest": digest}
    assert adapter().selected_model({"models": [model]}, digest) == model
    with pytest.raises(ValueError, match="identity"):
        adapter().selected_model({"models": [model]}, "0" * 64)
    with pytest.raises(ValueError, match="identity"):
        adapter().selected_model({"models": [model, model]}, digest)


def test_cli_requires_explicit_gate_and_fresh_output(tmp_path: Any) -> None:
    with pytest.raises(SystemExit):
        adapter().main(["--output", str(tmp_path / "new")])
    assert not (tmp_path / "new").exists()
    with pytest.raises(FileExistsError):
        adapter().run_experiment(tmp_path, model_digest="0" * 64)
