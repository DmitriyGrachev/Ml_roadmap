from uuid import uuid4

from .models import TicketCreate, TicketResponse


class TicketNotFound(Exception):
    """Raised when a ticket identifier is not present in this service instance."""


class TicketService:
    """A tiny in-memory boundary used to make application composition explicit."""

    def __init__(self) -> None:
        self._tickets: dict[str, TicketResponse] = {}

    def create(self, ticket: TicketCreate) -> TicketResponse:
        ticket_id = str(uuid4())
        created = TicketResponse(id=ticket_id, **ticket.model_dump())
        self._tickets[ticket_id] = created
        return created

    def get(self, ticket_id: str) -> TicketResponse:
        try:
            return self._tickets[ticket_id]
        except KeyError as error:
            raise TicketNotFound from error
