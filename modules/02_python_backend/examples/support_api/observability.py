import logging
from typing import Literal

type TicketEvent = Literal["created", "loaded"]


def log_ticket_event(
    logger: logging.Logger,
    *,
    ticket_id: str,
    event: TicketEvent,
) -> None:
    """Log safe, queryable ticket metadata without request-body contents."""

    logger.info(
        "support_ticket_event",
        extra={"ticket_id": ticket_id, "event": event},
    )
