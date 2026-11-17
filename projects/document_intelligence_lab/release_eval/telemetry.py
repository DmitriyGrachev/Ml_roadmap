"""Bounded loopback JSON transport and the small OTLP/HTTP trace subset used in this lab."""

import json
import re
from collections.abc import Iterator
from contextlib import closing, contextmanager
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from secrets import token_hex
from time import perf_counter_ns, time_ns
from typing import Any, Never
from urllib.parse import urlsplit

CHAT_PATH = "/v1/chat/completions"
TRACES_PATH = "/v1/traces"
_LOCAL_ORIGIN = r"https?://(?:127\.0\.0\.1|\[::1\]|localhost)(?::[0-9]{1,5})?"
_MAX_RESPONSE = 1024 * 1024


def validate_endpoint(url: str, path: str) -> str:
    """Accept only a complete, fixed local route, with no credentials or parameters."""
    if path not in {CHAT_PATH, TRACES_PATH} or not re.fullmatch(_LOCAL_ORIGIN + path, url):
        raise ValueError("invalid local endpoint")
    try:
        port = urlsplit(url).port
    except ValueError:
        raise ValueError("invalid endpoint port") from None
    if port == 0:
        raise ValueError("invalid endpoint port")
    return url


def _invalid_number(value: str) -> Never:
    raise ValueError("invalid JSON number")


def post_json(
    url: str, payload: object, token: str | None = None, *, timeout: float = 90.0
) -> dict[str, Any]:
    """One direct request. HTTPConnection does not use environment proxies or follow redirects."""
    path = CHAT_PATH if url.endswith(CHAT_PATH) else TRACES_PATH
    parts = urlsplit(validate_endpoint(url, path))
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token is not None:
        if path != CHAT_PATH or not re.fullmatch(r"[!-~]+", token):
            raise ValueError("invalid inference credential")
        headers["Authorization"] = "Bearer " + token
    connection = HTTPSConnection if parts.scheme == "https" else HTTPConnection
    with closing(connection(parts.hostname or "", parts.port, timeout=timeout)) as client:
        try:
            client.request("POST", path, json.dumps(payload, allow_nan=False).encode(), headers)
            response = client.getresponse()
            if response.status != 200:
                raise ValueError(f"endpoint HTTP {response.status}")
            if response.headers.get_content_type() != "application/json":
                raise ValueError("endpoint response must be application/json")
            body = response.read(_MAX_RESPONSE + 1)
        except (HTTPException, OSError):
            raise ValueError("local endpoint connection failed") from None
    if len(body) > _MAX_RESPONSE:
        raise ValueError("endpoint response exceeds size limit")
    try:
        result = json.loads(body.decode("utf-8"), parse_constant=_invalid_number)
    except (ValueError, RecursionError):
        raise ValueError("invalid endpoint JSON") from None
    if not isinstance(result, dict):
        raise ValueError("endpoint response must be a JSON object")
    return result


def _attribute(key: str, value: str) -> dict[str, object]:
    return {"key": key, "value": {"stringValue": value}}


class Trace:
    def __init__(self, spans: list[dict[str, Any]]) -> None:
        self.trace_id = token_hex(16)
        self.root_id = token_hex(8)
        self._spans = spans
        self._wall_start = time_ns()
        self._tick_start = perf_counter_ns()

    def _timestamp(self) -> str:
        # OTLP uses Unix nanoseconds. Durations use a monotonically increasing clock.
        return str(self._wall_start + (perf_counter_ns() - self._tick_start))

    @contextmanager
    def _record(self, span: dict[str, Any]) -> Iterator[None]:
        span["traceId"] = self.trace_id
        span["startTimeUnixNano"] = self._timestamp()
        self._spans.append(span)
        succeeded = False
        try:
            yield
            succeeded = True
        finally:
            span["endTimeUnixNano"] = self._timestamp()
            span["status"] = {"code": 1 if succeeded else 2}

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        if name not in {"retrieval", "generation"}:
            raise ValueError("unknown evaluation stage")
        with self._record(
            {"name": name, "kind": 1, "spanId": token_hex(8), "parentSpanId": self.root_id}
        ):
            yield


class Telemetry:
    def __init__(self) -> None:
        self._spans: list[dict[str, Any]] = []

    @contextmanager
    def request(self, case_id: str, release: str) -> Iterator[Trace]:
        """Labels must be opaque fixture and release IDs. No free-form text attributes."""
        if not all(re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", value) for value in (case_id, release)):
            raise ValueError("invalid trace label")
        trace = Trace(self._spans)
        with trace._record(
            {
                "name": "document.answer",
                "kind": 1,
                "spanId": trace.root_id,
                "attributes": [
                    _attribute("eval.case_id", case_id),
                    _attribute("eval.release", release),
                ],
            }
        ):
            yield trace

    def payload(self) -> dict[str, Any]:
        resource = {"attributes": [_attribute("service.name", "document-release-eval")]}
        scope = {"name": "roadmap.release_eval", "version": "1"}
        return {
            "resourceSpans": [
                {
                    "resource": resource,
                    "scopeSpans": [{"scope": scope, "spans": self._spans}],
                }
            ]
        }

    def export(self, url: str) -> None:
        response = post_json(validate_endpoint(url, TRACES_PATH), self.payload(), timeout=5)
        partial = response.get("partialSuccess", {})
        if (
            response.keys() - {"partialSuccess"}
            or not isinstance(partial, dict)
            or str(partial.get("rejectedSpans", 0)) != "0"
        ):
            raise ValueError("collector rejected spans or sent an invalid acknowledgement")
