"""Application factory for the Banking AI Lab API."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from banking_ai_lab.api import create_api_router
from banking_ai_lab.config import Settings
from banking_ai_lab.persistence import (
    SqlAlchemyTransactionRepository,
    create_database_engine,
    create_session_factory,
)
from banking_ai_lab.service import (
    DuplicateTransactionError,
    TransactionNotFoundError,
    TransactionService,
)

APP_TITLE = "Banking AI Lab API"
APP_VERSION = "0.1.0"


def _default_service(settings: Settings) -> tuple[TransactionService, object]:
    engine = create_database_engine(settings.database_url)
    sessions = create_session_factory(engine)
    repository = SqlAlchemyTransactionRepository(sessions)
    return TransactionService(repository), engine


def create_app(service: TransactionService | None = None) -> FastAPI:
    """Create an independent configured app without opening a database connection."""
    settings = Settings()
    app = FastAPI(title=APP_TITLE, version=APP_VERSION)

    if service is not None:
        selected_service = service
        engine: object | None = None
    else:
        selected_service, engine = _default_service(settings)

    app.state.settings = settings
    app.state.transaction_service = selected_service
    app.state.database_engine = engine

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(DuplicateTransactionError)
    async def duplicate_transaction_handler(
        _request: Request,
        _exception: DuplicateTransactionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "code": "duplicate_transaction",
                    "message": "Transaction already exists",
                }
            },
        )

    @app.exception_handler(TransactionNotFoundError)
    async def transaction_not_found_handler(
        _request: Request,
        _exception: TransactionNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": {
                    "code": "transaction_not_found",
                    "message": "Transaction not found",
                }
            },
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(_request: Request, _exception: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "code": "internal_error",
                    "message": "Internal server error",
                }
            },
        )

    app.include_router(create_api_router(settings.api_prefix))
    return app


app = create_app()
