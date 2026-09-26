"""Validate a tool proposal and check application-owned permission before a read."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BOOKS = {"B-001": "Atlas of Birds", "B-002": "A Short History of Clocks"}


class LookupArguments(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    book_id: str = Field(pattern=r"^B-[0-9]{3}$")


class LookupProposal(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    name: Literal["lookup_book"]
    arguments: LookupArguments


def lookup_book(raw_proposal: str, *, can_read: bool) -> str:
    """The caller derives can_read from authentication, never from model text."""
    if not can_read:
        raise PermissionError("catalog reading is not authorized")
    proposal = LookupProposal.model_validate_json(raw_proposal)
    return BOOKS[proposal.arguments.book_id]


def main() -> None:
    proposal = '{"name":"lookup_book","arguments":{"book_id":"B-001"}}'
    print(lookup_book(proposal, can_read=True))
    print("One allowlisted in-memory read; no model text is evaluated as code.")


if __name__ == "__main__":
    main()
