"""Author behaviors; these do not implement or extend student acceptance tests."""

import importlib
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

validation = importlib.import_module("modules.02_python_backend.02_pydantic.walkthrough")
transactions = importlib.import_module("modules.02_python_backend.06_sqlalchemy.walkthrough")
fixtures = importlib.import_module(
    "modules.02_python_backend.08_api_integration_testing.walkthrough"
)
plans = importlib.import_module("modules.02_python_backend.exercises.analytics_sql.plan_demo")
shelf_client = fixtures.shelf_client


@pytest.mark.parametrize(
    ("quantity", "error_type"), [(0, "value_error"), (6, "value_error"), ("oops", "int_parsing")]
)
def test_invalid_batch_reports_field_and_never_reaches_service(
    quantity: object, error_type: str
) -> None:
    app, service = validation.create_app()
    with TestClient(app) as client:
        response = client.post("/print-batches", json={"quantity": quantity})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert [(error["loc"], error["type"]) for error in errors] == [
        (["body", "quantity"], error_type)
    ]
    assert service.accepted == []


def test_batch_parses_then_passes_typed_quantity_to_service() -> None:
    app, service = validation.create_app()
    with TestClient(app) as client:
        response = client.post("/print-batches", json={"quantity": "8"})
    assert response.status_code == 201
    assert response.json() == {"quantity": 8, "packs": 2}
    assert service.accepted == [8]
    assert type(service.accepted[0]) is int


def test_failed_flush_rolls_back_all_new_labels_and_next_session_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ObservedSession(Session):
        """Retain real SQL/transaction behavior while observing resource ownership."""

        def __init__(self, bind: Engine) -> None:
            super().__init__(bind)
            self.rollback_count = 0
            self.closed = False
            sessions.append(self)

        def rollback(self) -> None:
            super().rollback()
            self.rollback_count += 1

        def close(self) -> None:
            super().close()
            self.closed = True

    sessions: list[ObservedSession] = []
    monkeypatch.setattr(transactions, "Session", ObservedSession)
    engine = create_engine(f"sqlite:///{tmp_path / 'labels.db'}")
    events: list[str] = []
    try:
        transactions.create_schema(engine)
        transactions.write_batch(engine, ["Atlas"], events)
        assert events == ["open", "pending=1", "flushed=1", "commit", "close"]
        assert len(sessions) == 1
        assert sessions[0].closed
        events.clear()
        with pytest.raises(IntegrityError):
            transactions.write_batch(engine, ["Beacon", "Atlas"], events)
        assert events == ["open", "pending=2", "rollback", "close"]
        assert len(sessions) == 2
        assert sessions[1].closed
        assert sessions[1].rollback_count == 1
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT name FROM labels ORDER BY name")
            ).scalars().all() == ["Atlas"]
        events.clear()
        transactions.write_batch(engine, ["Cedar"], events)
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT name FROM labels ORDER BY name")
            ).scalars().all() == [
                "Atlas",
                "Cedar",
            ]
        assert events[-2:] == ["commit", "close"]
        assert len(sessions) == 3
        assert sessions[2].closed
    finally:
        engine.dispose()


def test_shelf_fixture_exercises_real_route(shelf_client: Any) -> None:
    case = shelf_client
    response = case.client.post("/shelf-notes", json={"text": "Read chapter 2"})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "text": "Read chapter 2"}


@pytest.mark.parametrize("body_fails", [False, True], ids=["success", "exception"])
def test_client_cleanup_restores_app_and_fresh_case_has_no_notes(body_fails: bool) -> None:
    first = None
    outcome = (
        pytest.raises(ValueError, match="deliberate body failure") if body_fails else nullcontext()
    )
    with outcome, fixtures.client_scope() as case:
        first = case
        assert case.events == ["setup", "startup"]
        assert case.app.dependency_overrides
        response = case.client.post("/shelf-notes", json={"text": "Keep locally"})
        assert response.status_code == 201
        if body_fails:
            raise ValueError("deliberate body failure")
    assert first is not None
    assert first.app.dependency_overrides == {}
    assert first.events == ["setup", "startup", "shutdown", "teardown"]
    assert first.client.is_closed
    with fixtures.client_scope() as second:
        assert second.app is not first.app
        assert second.store is not first.store
        assert second.client.get("/shelf-notes").json() == []


def test_index_experiment_keeps_identical_ordered_rows() -> None:
    result = plans.run_experiment(size=3000, repeats=3)
    assert result.before_rows == [(17, 7), (1017, 7), (2017, 7)]
    assert result.after_rows == [(17, 7), (1017, 7), (2017, 7)]
    assert len(result.before_ms) == len(result.after_ms) == 3
    assert all(duration >= 0 for duration in result.before_ms + result.after_ms)
    assert result.index_pages > 0


def test_index_lookup_returns_empty_for_absent_zone() -> None:
    result = plans.run_experiment(size=30, repeats=2, zone="Z999")
    assert result.before_rows == result.after_rows == []


def test_real_pytest_failure_still_tears_down_yield_fixture(tmp_path: Path) -> None:
    probe = tmp_path / "fixture_probe.py"
    probe.write_text(
        """import importlib

lesson = importlib.import_module(
    "modules.02_python_backend.08_api_integration_testing.walkthrough"
)
shelf_client = lesson.shelf_client
observed = []


def test_deliberate_failure(shelf_client):
    observed.append(shelf_client)
    response = shelf_client.client.post("/shelf-notes", json={"text": "first test"})
    assert response.json() == {"id": 1, "text": "first test"}
    assert False, "intentional fixture-body failure"


def test_next_fixture_is_clean(shelf_client):
    first = observed[0]
    assert first.app.dependency_overrides == {}
    assert first.client.is_closed
    assert first.events == ["setup", "startup", "shutdown", "teardown"]
    assert shelf_client.app is not first.app
    assert shelf_client.client.get("/shelf-notes").json() == []
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(probe), "-q", "--import-mode=importlib"],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "1 failed, 1 passed" in result.stdout, result.stdout + result.stderr
    assert "intentional fixture-body failure" in result.stdout
