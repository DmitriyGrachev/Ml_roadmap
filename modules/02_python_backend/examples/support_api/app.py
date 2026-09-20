from collections.abc import Sequence

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse

from .config import SupportSettings
from .models import TicketCreate, TicketResponse
from .provider_status import ProviderStatus, StatusProvider, fetch_provider_statuses
from .service import TicketNotFound, TicketService


def create_app(
    service: TicketService | None = None,
    *,
    status_providers: Sequence[StatusProvider] | None = None,
    settings: SupportSettings | None = None,
) -> FastAPI:
    """Compose a fresh app with instance-owned storage and explicit integrations."""

    ticket_service = service if service is not None else TicketService()
    providers = tuple(status_providers) if status_providers is not None else ()
    app_settings = settings if settings is not None else SupportSettings()
    app = FastAPI(title=app_settings.app_name)
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
    def create_ticket(ticket: TicketCreate) -> TicketResponse:
        return ticket_service.create(ticket)

    @router.get("/tickets/{ticket_id}", response_model=TicketResponse)
    def get_ticket(ticket_id: str) -> TicketResponse:
        return ticket_service.get(ticket_id)

    @router.get("/provider-statuses", response_model=list[ProviderStatus])
    async def provider_statuses() -> list[ProviderStatus]:
        return await fetch_provider_statuses(providers)

    app.include_router(router)
    app.add_exception_handler(TicketNotFound, _ticket_not_found_handler)
    return app


async def _ticket_not_found_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": "ticket_not_found", "message": "Ticket was not found"},
    )
