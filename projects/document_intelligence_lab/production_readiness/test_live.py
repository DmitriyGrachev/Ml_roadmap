"""Explicit opt-in only; actual loopback sockets and bounded local child processes."""

import os
from pathlib import Path

import pytest

from .demo import run_demo
from .evidence import validate_lifecycle


@pytest.mark.optional_live
@pytest.mark.skipif(os.environ.get("ROADMAP_RUN_TCP") != "1", reason="set ROADMAP_RUN_TCP=1")
def test_real_tcp_restart_and_rollback(tmp_path: Path) -> None:
    output = run_demo(tmp_path / "tcp", requests=6, concurrency=2)
    assert validate_lifecycle(output, learner=False)["mechanical_status"] == "VERIFIED"
