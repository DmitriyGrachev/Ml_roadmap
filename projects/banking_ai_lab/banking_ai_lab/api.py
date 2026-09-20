"""Complete HTTP DTO and routing infrastructure for unfinished project services."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict

from banking_ai_lab.analytics import TransactionReport, build_report
from banking_ai_lab.domain import Currency, Transaction, TransactionStatus
from banking_ai_lab.service import TransactionService


class TransactionCreate(Transaction):
    """Validated HTTP request body for transaction creation."""


class TransactionResponse(Transaction):
    """Complete public representation of one transaction."""


class CurrencySummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    currency: Currency
    transaction_count: int
    total_amount: Decimal


class StatusSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: TransactionStatus
    transaction_count: int


class MerchantSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    merchant: str
    transaction_count: int
    total_amount: Decimal


class TransactionReportResponse(BaseModel):
    """Stable public report schema shared with Stage 2 analytics."""

    model_config = ConfigDict(frozen=True)

    transaction_count: int
    fraud_count: int
    period_start: datetime | None
    period_end: datetime | None
    currencies: tuple[CurrencySummaryResponse, ...]
    statuses: tuple[StatusSummaryResponse, ...]
    top_merchants: tuple[MerchantSummaryResponse, ...]

    @classmethod
    def from_report(cls, report: TransactionReport) -> TransactionReportResponse:
        return cls.model_validate(
            {
                "transaction_count": report.transaction_count,
                "fraud_count": report.fraud_count,
                "period_start": report.period_start,
                "period_end": report.period_end,
                "currencies": report.currencies,
                "statuses": report.statuses,
                "top_merchants": report.top_merchants,
            },
            from_attributes=True,
        )


def get_transaction_service(request: Request) -> TransactionService:
    """Resolve the service owned by this application instance."""
    return cast(TransactionService, request.app.state.transaction_service)


ServiceDependency = Annotated[TransactionService, Depends(get_transaction_service)]


def create_api_router(api_prefix: str) -> APIRouter:
    """Build one router under the already validated application prefix."""
    router = APIRouter(prefix=api_prefix)

    @router.post(
        "/transactions",
        response_model=TransactionResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_transaction(
        payload: TransactionCreate,
        service: ServiceDependency,
    ) -> Transaction:
        transaction = Transaction.model_validate(payload.model_dump())
        return service.create_transaction(transaction)

    @router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
    def get_transaction(transaction_id: UUID, service: ServiceDependency) -> Transaction:
        return service.get_transaction(transaction_id)

    @router.get("/transactions", response_model=list[TransactionResponse])
    def list_transactions(
        service: ServiceDependency,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 100,
        user_id: str | None = None,
        transaction_status: Annotated[TransactionStatus | None, Query(alias="status")] = None,
    ) -> tuple[Transaction, ...]:
        return service.list_transactions(
            offset=offset,
            limit=limit,
            user_id=user_id,
            status=transaction_status,
        )

    @router.get("/reports/summary", response_model=TransactionReportResponse)
    def summary_report(service: ServiceDependency) -> TransactionReportResponse:
        transactions = service.list_transactions(
            offset=0,
            limit=None,
            user_id=None,
            status=None,
        )
        return TransactionReportResponse.from_report(build_report(transactions))

    return router
