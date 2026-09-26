"""Student boundary for an in-memory library search API."""

from collections.abc import Sequence
from dataclasses import dataclass

from fastapi import FastAPI


@dataclass(frozen=True)
class Book:
    """One catalog entry; IDs are unique within an application."""

    id: str
    title: str
    author: str
    year: int
    available: bool


def create_app(books: Sequence[Book]) -> FastAPI:
    """Build an isolated application exposing the documented GET /books contract."""
    seen: set[str] = set()
    for book in books:
        if not all(
            isinstance(value, str) and value.strip() for value in (book.id, book.title, book.author)
        ):
            raise ValueError("book text fields must be nonblank")
        if book.id in seen:
            raise ValueError("book IDs must be unique")
        if type(book.year) is not int or not 1 <= book.year <= 9999:
            raise ValueError("book year must be an integer from 1 to 9999")
        if type(book.available) is not bool:
            raise ValueError("book availability must be a boolean")
        seen.add(book.id)
    # TODO: build the app, validate query parameters, and implement the search route.
    raise NotImplementedError("build library search application")
