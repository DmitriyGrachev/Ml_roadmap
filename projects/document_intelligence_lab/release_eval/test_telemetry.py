"""Check the OTLP/HTTP wire contract without opening a network socket."""

import json
import re
from http.client import HTTPConnection
from io import BytesIO
from unittest.mock import MagicMock

import pytest

from projects.document_intelligence_lab.release_eval.telemetry import (
    Telemetry,
    post_json,
    validate_endpoint,
)

ORIGIN = "http://127.0.0.1:4318"


def receiver(monkeypatch: pytest.MonkeyPatch, body: bytes, status: int = 200) -> bytearray:
    """Substitute only the socket. Real HTTPConnection serializes and parses the exchange."""
    wire = bytearray()
    sock = MagicMock()
    sock.sendall.side_effect = wire.extend
    reply = (
        f"HTTP/1.1 {status} Reply\r\nContent-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\nLocation: /v1/traces\r\n\r\n"
    ).encode()
    sock.makefile.return_value = BytesIO(reply + body)

    def connect(client: HTTPConnection) -> None:
        client.sock = sock

    monkeypatch.setattr(HTTPConnection, "connect", connect)
    return wire


def test_trace_export_correlates_per_case_stages(monkeypatch: pytest.MonkeyPatch) -> None:
    telemetry = Telemetry()
    with telemetry.request("q-hours", "baseline") as trace:
        with trace.stage("retrieval"):
            pass
        with trace.stage("generation"):
            pass
    received = receiver(monkeypatch, b"{}")
    telemetry.export(ORIGIN + "/v1/traces")
    head, _, body = received.partition(b"\r\n\r\n")
    assert head.startswith(b"POST /v1/traces HTTP/1.1\r\n")
    assert b"Content-Type: application/json" in head
    assert b"Authorization:" not in head
    assert json.loads(body) == telemetry.payload()
    spans = json.loads(body)["resourceSpans"][0]["scopeSpans"][0]["spans"]
    by_name = {span["name"]: span for span in spans}
    assert set(by_name) == {"document.answer", "retrieval", "generation"}
    root = by_name["document.answer"]
    assert {s["traceId"] for s in spans} == {trace.trace_id}
    assert re.fullmatch("[a-f0-9]{32}", trace.trace_id)
    assert len({s["spanId"] for s in spans}) == 3
    for s in spans:
        assert re.fullmatch("[a-f0-9]{16}", s["spanId"])
        assert int(root["startTimeUnixNano"]) <= int(s["startTimeUnixNano"])
        assert int(s["startTimeUnixNano"]) <= int(s["endTimeUnixNano"])
        assert int(s["endTimeUnixNano"]) <= int(root["endTimeUnixNano"])
        if s is not root:
            assert s["parentSpanId"] == root["spanId"]


def test_failed_stage_records_status_without_error_text() -> None:
    telemetry = Telemetry()
    with (
        pytest.raises(RuntimeError, match="sensitive"),
        telemetry.request("q-1", "v1") as trace,
        trace.stage("generation"),
    ):
        raise RuntimeError("sensitive")
    payload = telemetry.payload()
    assert "sensitive" not in json.dumps(payload)
    spans = payload["resourceSpans"][0]["scopeSpans"][0]["spans"]
    assert all(s["status"]["code"] == 2 for s in spans)


@pytest.mark.parametrize(
    "url",
    [
        "http://outside.invalid/v1/traces",
        "http://u:p@127.0.0.1/v1/traces",
        "http://127.0.0.1/v1/traces?key=x",
        "http://127.0.0.1/v1/traces#secret",
        "http://127.0.0.1/v1/chat/completions",
        "http://localhost:70000/v1/traces",
    ],
)
def test_rejects_unsafe_collector_endpoint(url: str) -> None:
    with pytest.raises(ValueError, match="endpoint"):
        validate_endpoint(url, "/v1/traces")


@pytest.mark.parametrize(
    "body",
    [
        b'{"partialSuccess":{"rejectedSpans":"1","errorMessage":"private"}}',
        b'{"error":"private"}',
    ],
)
def test_collector_must_acknowledge_all_spans(body: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    receiver(monkeypatch, body)
    with pytest.raises(ValueError, match="acknowledgement") as error:
        Telemetry().export(ORIGIN + "/v1/traces")
    assert "private" not in str(error.value)


def test_completion_transport_does_not_follow_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    received = receiver(monkeypatch, b"{}", 307)
    with pytest.raises(ValueError, match="307"):
        post_json(ORIGIN + "/v1/chat/completions", {}, "testing")
    assert b"Authorization: Bearer testing" in received
    assert b"/v1/traces" not in received


@pytest.mark.parametrize(
    "body",
    [b"[]", b'{"value":NaN}', b"not JSON", b"x" * 1_048_577],
    ids=["array", "invalid-number", "malformed", "too-large"],
)
def test_invalid_provider_response_fails_closed(
    body: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    receiver(monkeypatch, body)
    with pytest.raises(ValueError, match="endpoint"):
        post_json(ORIGIN + "/v1/chat/completions", {})
