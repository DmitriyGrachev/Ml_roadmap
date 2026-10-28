"""Author checks for the separate Module 05 teacher walkthrough."""

import importlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

walkthrough = importlib.import_module("modules.05_llm_engineering.walkthrough")


def test_request_discloses_only_authorized_guide() -> None:
    public = walkthrough.build_request("Can I leave a bicycle overnight?", "public")
    assert public is not None
    assert public.context_id == "G-01"
    assert public.context_version == "2026-09"
    assert public.context_access == "public"
    assert "Pickup by 19:00" in public.context
    assert "staff access code" not in public.context
    assert walkthrough.build_request("What is the staff access code?", "visitor") is None


def test_budget_counts_all_fictional_request_parts_and_reserves_output() -> None:
    budget = walkthrough.account_budget(
        limit=100, framing=12, instruction=20, question=10, context=35, tools=3, reserve=20
    )
    assert budget.input_units == 80
    assert budget.remaining == 0
    demo_parts = walkthrough.build_demo()["budget"]
    assert demo_parts == {
        "limit": 100,
        "framing": 15,
        "instruction": 20,
        "question": 10,
        "context": 35,
        "tools": 0,
        "input_units": 80,
        "reserve": 20,
        "remaining": 0,
    }
    with pytest.raises(ValueError, match="budget"):
        walkthrough.account_budget(
            limit=99, framing=12, instruction=20, question=10, context=35, tools=3, reserve=20
        )


@pytest.mark.parametrize(
    ("raw", "finish", "expected"),
    [
        (
            '{"status":"unavailable","next_step":"none","evidence_id":"G-01",'
            '"evidence_quote":"Overnight storage is not offered."}',
            "stop",
            "accepted",
        ),
        ("", "stop", "empty"),
        ("{broken", "stop", "schema_failure"),
        (
            '{"status":"unavailable","next_step":"visit","evidence_id":"G-01",'
            '"evidence_quote":"Overnight storage is not offered."}',
            "stop",
            "semantic_failure",
        ),
        (
            '{"status":"available","next_step":"visit","evidence_id":"G-01",'
            '"evidence_quote":"Pickup by 19:00."}',
            "stop",
            "evidence_failure",
        ),
        ("", "refusal", "refused"),
        ('{"status":"unavailable"', "length", "truncated"),
    ],
)
def test_completion_gates(raw: str, finish: str, expected: str) -> None:
    request = walkthrough.build_request("Can I leave a bicycle overnight?", "public")
    assert request is not None
    assert walkthrough.decide_completion(raw, finish, request).stage == expected


def test_answer_for_one_question_cannot_validate_another_request() -> None:
    unrelated = walkthrough.build_request("What does repair cost?", "public")
    assert unrelated is not None
    assert (
        walkthrough.decide_completion(walkthrough.SUCCESS, "stop", unrelated).stage
        == "evidence_failure"
    )
    protected = walkthrough.build_request("What is the staff access code?", "staff")
    assert protected is not None
    assert (
        walkthrough.decide_completion(walkthrough.SUCCESS, "stop", protected).stage
        == "evidence_failure"
    )
    current = walkthrough.build_request("Can I leave a bicycle overnight?", "public")
    assert current is not None
    old = replace(current, context_version="2025-01")
    assert (
        walkthrough.decide_completion(walkthrough.SUCCESS, "stop", old).stage == "evidence_failure"
    )


def test_denied_access_does_not_build_model_request() -> None:
    trace = walkthrough.make_trace("visitor", "What is the staff access code?")
    assert trace["decision"]["stage"] == "access_denied"
    assert trace["request"] is None
    assert trace["completion"] is None


def test_cli_offline_deterministic_and_preserves_existing_output(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    command = [sys.executable, "-m", "modules.05_llm_engineering.walkthrough"]
    environment = {**os.environ, "NO_PROXY": "*", "HTTP_PROXY": "", "HTTPS_PROXY": ""}
    subprocess.run([*command, "--output", str(first)], check=True, env=environment)
    subprocess.run([*command, "--output", str(second)], check=True, env=environment)
    assert (first / "trace.json").read_bytes() == (second / "trace.json").read_bytes()
    trace = json.loads((first / "trace.json").read_text(encoding="utf-8"))
    assert trace["cases"]["success"]["decision"]["stage"] == "accepted"
    assert trace["cases"]["unsupported"]["decision"]["stage"] == "evidence_failure"
    before = (first / "trace.json").read_bytes()
    rerun = subprocess.run([*command, "--output", str(first)], capture_output=True, env=environment)
    assert rerun.returncode != 0
    assert (first / "trace.json").read_bytes() == before
    empty = tmp_path / "existing-empty"
    empty.mkdir()
    assert subprocess.run([*command, "--output", str(empty)], capture_output=True).returncode != 0


def test_import_and_run_cannot_open_socket(tmp_path: Path) -> None:
    script = (
        "import runpy, socket, sys; "
        "socket.socket.connect = lambda *a, **k: 1/0; "
        "socket.create_connection = lambda *a, **k: 1/0; "
        "sys.argv = ['walkthrough', '--output', sys.argv[1]]; "
        "runpy.run_module('modules.05_llm_engineering.walkthrough', run_name='__main__')"
    )
    subprocess.run([sys.executable, "-c", script, str(tmp_path / "offline")], check=True)
    assert (tmp_path / "offline" / "trace.json").exists()
