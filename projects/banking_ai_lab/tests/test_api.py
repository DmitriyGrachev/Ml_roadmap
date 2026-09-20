"""Stage 4 configuration, application, and HTTP acceptance contracts."""

from __future__ import annotations

import re
import warnings
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from banking_ai_lab.analytics import (
    CurrencySummary,
    MerchantSummary,
    StatusSummary,
    TransactionReport,
)
from banking_ai_lab.api import TransactionReportResponse
from banking_ai_lab.app import APP_TITLE, APP_VERSION, create_app
from banking_ai_lab.config import Settings
from banking_ai_lab.domain import Transaction, TransactionStatus
from banking_ai_lab.service import (
    DuplicateTransactionError,
    TransactionNotFoundError,
    TransactionRepository,
    TransactionService,
)
from fastapi import FastAPI
from pydantic import ValidationError
from starlette.exceptions import StarletteDeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=StarletteDeprecationWarning)
    warnings.filterwarnings(
        "ignore",
        message="The anyio.abc.BlockingPortal alias is deprecated.*",
        category=DeprecationWarning,
    )
    from starlette.testclient import TestClient

from roadmap_tools import exercise_call

PROJECT_ROOT = Path(__file__).parents[1]
API_PREFIX = "/api"


def make_transaction(
    index: int,
    *,
    amount: str = "10.25",
    currency: str = "EUR",
    user_id: str | None = None,
    timestamp: datetime | None = None,
    status: str = "approved",
    category: str | None = "groceries",
    is_fraud: bool = False,
) -> Transaction:
    return Transaction.model_validate(
        {
            "id": UUID(int=index),
            "user_id": user_id or f"user-{index:04d}",
            "amount": Decimal(amount),
            "currency": currency,
            "merchant": f"Merchant {index}",
            "category": category,
            "timestamp": timestamp or datetime(2025, 1, index, 10, tzinfo=UTC),
            "status": status,
            "is_fraud": is_fraud,
        }
    )


def request_json(transaction: Transaction) -> dict[str, object]:
    return {
        "id": str(transaction.id),
        "user_id": transaction.user_id,
        "amount": str(transaction.amount),
        "currency": transaction.currency,
        "merchant": transaction.merchant,
        "category": transaction.category,
        "timestamp": transaction.timestamp.isoformat().replace("+00:00", "Z"),
        "status": transaction.status,
        "is_fraud": transaction.is_fraud,
    }


def response_json(transaction: Transaction) -> dict[str, object]:
    return request_json(transaction)


class FakeRepository(TransactionRepository):
    """Deterministic in-memory repository used only to isolate service exercises."""

    def __init__(self, transactions: tuple[Transaction, ...] = ()) -> None:
        self.items = {transaction.id: transaction for transaction in transactions}
        self.create_calls: list[Transaction] = []
        self.get_calls: list[UUID] = []
        self.list_calls: list[tuple[int, int | None, str | None, TransactionStatus | None]] = []

    def create_transaction(self, transaction: Transaction) -> Transaction:
        self.create_calls.append(transaction)
        if transaction.id in self.items:
            raise DuplicateTransactionError(transaction.id)
        self.items[transaction.id] = transaction
        return transaction

    def get_transaction(self, transaction_id: UUID) -> Transaction | None:
        self.get_calls.append(transaction_id)
        return self.items.get(transaction_id)

    def list_transactions(
        self,
        *,
        offset: int,
        limit: int | None,
        user_id: str | None,
        status: TransactionStatus | None,
    ) -> tuple[Transaction, ...]:
        self.list_calls.append((offset, limit, user_id, status))
        matching = (
            transaction
            for transaction in self.items.values()
            if (user_id is None or transaction.user_id == user_id)
            and (status is None or transaction.status == status)
        )
        ordered = sorted(matching, key=lambda item: (item.timestamp, item.id))
        if limit is None:
            return tuple(ordered[offset:])
        return tuple(ordered[offset : offset + limit])


class FailingRepository(TransactionRepository):
    """Repository fake that exposes whether services preserve unrelated failures."""

    def __init__(self, error: BaseException) -> None:
        self.error = error
        self.calls: list[tuple[str, object]] = []

    def create_transaction(self, transaction: Transaction) -> Transaction:
        self.calls.append(("create", transaction))
        raise self.error

    def get_transaction(self, transaction_id: UUID) -> Transaction | None:
        self.calls.append(("get", transaction_id))
        raise self.error

    def list_transactions(
        self,
        *,
        offset: int,
        limit: int | None,
        user_id: str | None,
        status: TransactionStatus | None,
    ) -> tuple[Transaction, ...]:
        self.calls.append(("list", (offset, limit, user_id, status)))
        raise self.error


class ControlledService:
    """Complete API-plumbing fake that never implements a student service algorithm."""

    def __init__(self) -> None:
        self.created: Transaction | None = None
        self.fetched: Transaction | None = None
        self.listed: tuple[Transaction, ...] = ()
        self.error: BaseException | None = None
        self.calls: list[tuple[str, object]] = []

    def create_transaction(self, transaction: Transaction) -> Transaction:
        self.calls.append(("create", transaction))
        if self.error is not None:
            raise self.error
        return self.created or transaction

    def get_transaction(self, transaction_id: UUID) -> Transaction:
        self.calls.append(("get", transaction_id))
        if self.error is not None:
            raise self.error
        if self.fetched is None:
            raise AssertionError("controlled get result was not configured")
        return self.fetched

    def list_transactions(
        self,
        *,
        offset: int,
        limit: int | None,
        user_id: str | None,
        status: TransactionStatus | None,
    ) -> tuple[Transaction, ...]:
        self.calls.append(("list", (offset, limit, user_id, status)))
        if self.error is not None:
            raise self.error
        return self.listed


class FalseyService(ControlledService):
    def __bool__(self) -> bool:
        return False


@pytest.fixture
def isolated_app() -> Iterator[FastAPI]:
    app = create_app(cast(TransactionService, ControlledService()))
    yield app
    app.dependency_overrides.clear()


def test_settings_defaults_and_environment_names(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("BANKING_DATABASE_URL", "BANKING_LOG_LEVEL", "BANKING_API_PREFIX"):
        monkeypatch.delenv(name, raising=False)

    defaults = Settings()

    assert defaults.database_url.startswith("sqlite")
    assert defaults.log_level == "INFO"
    assert defaults.api_prefix == API_PREFIX

    monkeypatch.setenv("BANKING_DATABASE_URL", "sqlite:///custom-lab.db")
    monkeypatch.setenv("BANKING_LOG_LEVEL", "warning")
    monkeypatch.setenv("BANKING_API_PREFIX", "/banking/v1")
    configured = Settings()

    assert configured.database_url == "sqlite:///custom-lab.db"
    assert configured.log_level == "WARNING"
    assert configured.api_prefix == "/banking/v1"


@pytest.mark.parametrize("prefix", ["", "api", " api", "/api/", "//api"])
def test_settings_rejects_an_invalid_api_prefix(prefix: str) -> None:
    with pytest.raises(ValidationError):
        Settings(api_prefix=prefix)


@pytest.mark.parametrize("level", ["TRACE", "NOTICE", "", "info "])
def test_settings_rejects_an_unknown_or_malformed_log_level(level: str) -> None:
    with pytest.raises(ValidationError):
        Settings(log_level=level)


def test_application_factory_has_fixed_metadata_and_complete_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BANKING_API_PREFIX", API_PREFIX)
    app = create_app(cast(TransactionService, ControlledService()))

    with TestClient(app) as client:
        response = client.get("/health")

    assert app.title == APP_TITLE == "Banking AI Lab API"
    assert app.version == APP_VERSION == "0.1.0"
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_application_instances_never_share_state_or_dependency_overrides() -> None:
    first = create_app()
    second = create_app()

    def sentinel() -> None:
        return None

    first.dependency_overrides[sentinel] = lambda: "changed"

    assert first is not second
    assert first.state.transaction_service is not second.state.transaction_service
    assert sentinel not in second.dependency_overrides


def test_application_factory_selects_a_falsey_injected_service() -> None:
    injected = FalseyService()

    app = create_app(cast(TransactionService, injected))

    assert app.state.transaction_service is injected


def test_application_construction_and_health_do_not_create_the_sqlite_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "not-created-during-app-construction.db"
    monkeypatch.setenv("BANKING_DATABASE_URL", f"sqlite:///{database.as_posix()}")

    app = create_app()
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200

    assert not database.exists()


def test_configured_prefix_owns_routes_without_moving_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BANKING_API_PREFIX", "/banking/v1")
    service = ControlledService()
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/transactions").status_code == 404
        response = client.get("/banking/v1/transactions", params={"limit": 0})

    assert response.status_code == 422
    assert service.calls == []


def test_fixture_cleanup_clears_dependency_overrides(isolated_app: FastAPI) -> None:
    def dependency() -> str:
        return "original"

    isolated_app.dependency_overrides[dependency] = lambda: "override"
    assert isolated_app.dependency_overrides


@pytest.mark.student_exercise
def test_post_transaction_returns_complete_201_json() -> None:
    transaction = make_transaction(1, amount="12.30", category=None, is_fraud=True)
    repository = FakeRepository()
    app = create_app(TransactionService(repository))

    with TestClient(app) as client:
        response = exercise_call(
            client.post,
            f"{API_PREFIX}/transactions",
            json=request_json(transaction),
        )

    assert response.status_code == 201
    assert response.json() == response_json(transaction)
    assert repository.create_calls == [transaction]


@pytest.mark.student_exercise
def test_service_create_preserves_unrelated_repository_exception_identity() -> None:
    original = RuntimeError("create-sentinel")
    repository = FailingRepository(original)
    service = TransactionService(repository)
    transaction = make_transaction(21)

    with pytest.raises(RuntimeError) as caught:
        exercise_call(service.create_transaction, transaction)

    assert caught.value is original
    assert repository.calls == [("create", transaction)]


def test_duplicate_transaction_maps_to_a_stable_safe_409() -> None:
    transaction = make_transaction(1)
    service = ControlledService()
    service.error = DuplicateTransactionError(transaction.id, internal_detail="db-secret-409")
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        response = client.post(f"{API_PREFIX}/transactions", json=request_json(transaction))

    assert response.status_code == 409
    assert response.json() == {
        "detail": {
            "code": "duplicate_transaction",
            "message": "Transaction already exists",
        }
    }
    assert "db-secret-409" not in response.text


@pytest.mark.student_exercise
def test_service_duplicate_from_directly_seeded_repository_reaches_the_409_contract() -> None:
    transaction = make_transaction(1)
    repository = FakeRepository((transaction,))
    app = create_app(TransactionService(repository))

    with TestClient(app) as client:
        response = exercise_call(
            client.post,
            f"{API_PREFIX}/transactions",
            json=request_json(transaction),
        )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "duplicate_transaction"
    assert repository.create_calls == [transaction]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount", "0.00"),
        ("currency", "CAD"),
        ("timestamp", "2025-01-01T10:00:00"),
    ],
)
def test_post_validation_is_field_specific_and_never_calls_service(
    field: str,
    value: str,
) -> None:
    transaction = make_transaction(1)
    payload = request_json(transaction)
    payload[field] = value
    service = ControlledService()
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        response = client.post(f"{API_PREFIX}/transactions", json=payload)

    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    assert service.calls == []


@pytest.mark.student_exercise
def test_get_transaction_returns_complete_200_json_from_directly_seeded_state() -> None:
    transaction = make_transaction(7, amount="99.99", currency="GBP", status="refunded")
    repository = FakeRepository((transaction,))
    app = create_app(TransactionService(repository))

    with TestClient(app) as client:
        response = exercise_call(client.get, f"{API_PREFIX}/transactions/{transaction.id}")

    assert response.status_code == 200
    assert response.json() == response_json(transaction)
    assert repository.get_calls == [transaction.id]


@pytest.mark.student_exercise
def test_service_get_preserves_unrelated_repository_exception_identity() -> None:
    original = RuntimeError("get-sentinel")
    repository = FailingRepository(original)
    service = TransactionService(repository)
    transaction_id = UUID(int=92)

    with pytest.raises(RuntimeError) as caught:
        exercise_call(service.get_transaction, transaction_id)

    assert caught.value is original
    assert repository.calls == [("get", transaction_id)]


def test_missing_transaction_maps_to_a_stable_safe_404() -> None:
    transaction_id = UUID(int=404)
    service = ControlledService()
    service.error = TransactionNotFoundError(transaction_id, internal_detail="db-secret-404")
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        response = client.get(f"{API_PREFIX}/transactions/{transaction_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "transaction_not_found",
            "message": "Transaction not found",
        }
    }
    assert "db-secret-404" not in response.text


@pytest.mark.student_exercise
def test_service_missing_from_empty_repository_reaches_the_404_contract() -> None:
    transaction_id = UUID(int=405)
    repository = FakeRepository()
    app = create_app(TransactionService(repository))

    with TestClient(app) as client:
        response = exercise_call(client.get, f"{API_PREFIX}/transactions/{transaction_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "transaction_not_found"
    assert repository.get_calls == [transaction_id]


def test_malformed_transaction_id_is_rejected_before_calling_service() -> None:
    service = ControlledService()
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        response = client.get(f"{API_PREFIX}/transactions/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "transaction_id"]
    assert service.calls == []


@pytest.mark.student_exercise
def test_list_transactions_is_stably_ordered_and_forwards_explicit_filters() -> None:
    first = make_transaction(
        10,
        user_id="selected-user",
        timestamp=datetime(2025, 1, 2, 10, tzinfo=UTC),
        status="approved",
    )
    second = make_transaction(
        2,
        user_id="selected-user",
        timestamp=datetime(2025, 1, 1, 10, tzinfo=UTC),
        status="approved",
    )
    third = make_transaction(
        1,
        user_id="selected-user",
        timestamp=datetime(2025, 1, 1, 10, tzinfo=UTC),
        status="approved",
    )
    excluded = make_transaction(3, user_id="other-user", status="declined")
    repository = FakeRepository((first, second, third, excluded))
    app = create_app(TransactionService(repository))

    with TestClient(app) as client:
        response = exercise_call(
            client.get,
            f"{API_PREFIX}/transactions",
            params={
                "offset": 1,
                "limit": 1,
                "user_id": "selected-user",
                "status": "approved",
            },
        )

    assert response.status_code == 200
    assert response.json() == [response_json(second)]
    assert repository.list_calls == [(1, 1, "selected-user", "approved")]


@pytest.mark.parametrize(
    "params",
    [
        {"offset": -1},
        {"limit": 0},
        {"limit": 101},
    ],
)
def test_invalid_pagination_is_rejected_before_calling_service(params: dict[str, int]) -> None:
    service = ControlledService()
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        response = client.get(f"{API_PREFIX}/transactions", params=params)

    assert response.status_code == 422
    assert service.calls == []


def test_unknown_status_filter_is_rejected_before_calling_service() -> None:
    service = ControlledService()
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        response = client.get(f"{API_PREFIX}/transactions", params={"status": "unknown"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "status"]
    assert service.calls == []


@pytest.mark.student_exercise
def test_service_list_forwards_an_unbounded_request_independently() -> None:
    first = make_transaction(1)
    second = make_transaction(2)
    repository = FakeRepository((second, first))
    service = TransactionService(repository)

    transactions = exercise_call(
        service.list_transactions,
        offset=1,
        limit=None,
        user_id=None,
        status=None,
    )

    assert transactions == (second,)
    assert repository.list_calls == [(1, None, None, None)]


@pytest.mark.student_exercise
def test_service_list_preserves_unrelated_repository_exception_identity() -> None:
    original = RuntimeError("list-sentinel")
    repository = FailingRepository(original)
    service = TransactionService(repository)

    with pytest.raises(RuntimeError) as caught:
        exercise_call(
            service.list_transactions,
            offset=3,
            limit=7,
            user_id="selected-user",
            status="declined",
        )

    assert caught.value is original
    assert repository.calls == [("list", (3, 7, "selected-user", "declined"))]


def test_report_response_dto_serializes_the_complete_schema_without_student_algorithms() -> None:
    report = TransactionReport(
        transaction_count=2,
        fraud_count=1,
        period_start=datetime(2025, 1, 1, 10, tzinfo=UTC),
        period_end=datetime(2025, 1, 2, 10, tzinfo=UTC),
        currencies=(CurrencySummary("EUR", 2, Decimal("0.30")),),
        statuses=(
            StatusSummary("approved", 1),
            StatusSummary("declined", 1),
        ),
        top_merchants=(MerchantSummary("Merchant 2", 1, Decimal("0.20")),),
    )

    payload = TransactionReportResponse.from_report(report).model_dump(mode="json")

    assert payload == {
        "transaction_count": 2,
        "fraud_count": 1,
        "period_start": "2025-01-01T10:00:00Z",
        "period_end": "2025-01-02T10:00:00Z",
        "currencies": [{"currency": "EUR", "transaction_count": 2, "total_amount": "0.30"}],
        "statuses": [
            {"status": "approved", "transaction_count": 1},
            {"status": "declined", "transaction_count": 1},
        ],
        "top_merchants": [
            {"merchant": "Merchant 2", "transaction_count": 1, "total_amount": "0.20"}
        ],
    }


@pytest.mark.student_exercise
def test_summary_report_returns_the_complete_deterministic_schema() -> None:
    first = make_transaction(1, amount="0.10", currency="EUR", is_fraud=True)
    second = make_transaction(2, amount="0.20", currency="EUR", status="declined")
    service = ControlledService()
    service.listed = (first, second)
    app = create_app(cast(TransactionService, service))

    with TestClient(app) as client:
        response = exercise_call(client.get, f"{API_PREFIX}/reports/summary")

    assert response.status_code == 200
    assert response.json() == {
        "transaction_count": 2,
        "fraud_count": 1,
        "period_start": "2025-01-01T10:00:00Z",
        "period_end": "2025-01-02T10:00:00Z",
        "currencies": [{"currency": "EUR", "transaction_count": 2, "total_amount": "0.30"}],
        "statuses": [
            {"status": "approved", "transaction_count": 1},
            {"status": "declined", "transaction_count": 1},
        ],
        "top_merchants": [
            {"merchant": "Merchant 2", "transaction_count": 1, "total_amount": "0.20"},
            {"merchant": "Merchant 1", "transaction_count": 1, "total_amount": "0.10"},
        ],
    }
    assert service.calls == [("list", (0, None, None, None))]


def test_unrelated_exceptions_propagate_in_test_mode_and_are_generic_in_production_mode() -> None:
    original = RuntimeError("internal-secret-sentinel")
    service = ControlledService()
    service.error = original
    app = create_app(cast(TransactionService, service))

    with (
        TestClient(app, raise_server_exceptions=True) as client,
        pytest.raises(RuntimeError) as caught,
    ):
        client.get(f"{API_PREFIX}/transactions")
    assert caught.value is original

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(f"{API_PREFIX}/transactions")
    assert response.status_code == 500
    assert response.json() == {
        "detail": {"code": "internal_error", "message": "Internal server error"}
    }
    assert "internal-secret-sentinel" not in response.text


def test_environment_example_dockerfile_and_compose_are_safe_and_consistent() -> None:
    env_text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")

    env_keys = {
        line.split("=", 1)[0]
        for line in env_text.splitlines()
        if line and not line.startswith("#") and "=" in line
    }
    assert env_keys == {
        "BANKING_DATABASE_URL",
        "BANKING_LOG_LEVEL",
        "BANKING_API_PREFIX",
        "BANKING_POSTGRES_USER",
        "BANKING_POSTGRES_PASSWORD",
        "BANKING_POSTGRES_DB",
        "BANKING_POSTGRES_PORT",
        "BANKING_APP_PORT",
        "ROADMAP_POSTGRES_URL",
    }
    compose_variables = set(re.findall(r"\$\{([A-Z][A-Z0-9_]*)", compose))
    assert compose_variables <= env_keys
    assert "replace" in env_text.lower()

    first_line = dockerfile.splitlines()[0]
    assert first_line.startswith("FROM ghcr.io/astral-sh/uv:")
    assert ":latest" not in first_line
    assert re.search(r"(?m)^COPY\s+\.(?:/)?\s", dockerfile) is None
    assert "ADD " not in dockerfile
    assert ".env" not in dockerfile
    assert "__pycache__" not in dockerfile
    assert "uv sync --frozen --no-dev" in dockerfile
    assert "USER banking" in dockerfile
    assert "--app-dir" in dockerfile
    assert "projects/banking_ai_lab" in dockerfile

    services = compose.split("services:", 1)[1].split("\nvolumes:\n", 1)[0]
    assert set(re.findall(r"^  ([a-z][a-z0-9_-]*):\s*$", services, re.MULTILINE)) == {
        "app",
        "postgres",
    }
    assert "context: ../.." in compose
    assert "dockerfile: projects/banking_ai_lab/Dockerfile" in compose
    assert compose.count('"127.0.0.1:${') == 2
    assert "pg_isready" in compose
    assert "condition: service_healthy" in compose
    assert "postgres_data:" in compose
    assert "postgres_data:/var/lib/postgresql/data" in compose


@pytest.mark.parametrize(
    ("stage", "prerequisite", "minutes", "editable_names", "command"),
    [
        (
            "04_fastapi",
            "../03_pandas_analysis/README.md",
            "60-90 minutes",
            ("create_transaction", "get_transaction", "list_transactions"),
            "uv run pytest projects/banking_ai_lab/tests/test_api.py -q -rx",
        ),
        (
            "05_postgresql",
            "../04_fastapi/README.md",
            "75-90 minutes",
            ("SqlAlchemyTransactionRepository", "ROADMAP_POSTGRES_URL"),
            "uv run pytest -m postgres "
            "projects/banking_ai_lab/tests/test_postgres_integration.py -q -rs",
        ),
        (
            "06_testing",
            "../05_postgresql/README.md",
            "30-45 minutes",
            ("test_api.py", "test_persistence.py", "test_postgres_integration.py"),
            "uv run pytest projects/banking_ai_lab -q -rx",
        ),
    ],
)
def test_stage_guides_are_actionable_and_do_not_supply_business_algorithms(
    stage: str,
    prerequisite: str,
    minutes: str,
    editable_names: tuple[str, ...],
    command: str,
) -> None:
    readme = PROJECT_ROOT / "stages" / stage / "README.md"
    text = readme.read_text(encoding="utf-8")

    assert "## Prerequisites" in text
    assert f"]({prerequisite})" in text
    assert (readme.parent / prerequisite).resolve().is_file()
    assert "## Editable surface" in text
    assert minutes in text
    assert command in text
    assert "## Acceptance criteria" in text
    assert "## Hints" in text
    assert "## Cleanup" in text
    assert "## Completion checklist" in text
    for name in editable_names:
        assert name in text
    assert "Complete implementation:" not in text


def test_stage_five_documents_database_bootstrap_and_sqlite_numeric_scope() -> None:
    text = (PROJECT_ROOT / "stages" / "05_postgresql" / "README.md").read_text(encoding="utf-8")

    assert "create_schema(engine)" in text
    assert "docker compose up -d app" in text
    assert "SQLite" in text
    assert "aggregate" in text
    assert "PostgreSQL" in text
