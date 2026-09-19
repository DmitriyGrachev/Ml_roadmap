from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse

from .models import TicketCreate, TicketResponse
from .service import TicketNotFound, TicketService


def create_app(service: TicketService | None = None) -> FastAPI:
    """Compose a fresh FastAPI application with an instance-owned ticket store."""

    ticket_service = service or TicketService()
    app = FastAPI(title="Support ticket example")
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

    app.include_router(router)
    app.add_exception_handler(TicketNotFound, _ticket_not_found_handler)
    return app


async def _ticket_not_found_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": "ticket_not_found", "message": "Ticket was not found"},
    )
