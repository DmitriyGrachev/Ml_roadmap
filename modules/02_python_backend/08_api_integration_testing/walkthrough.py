"""Teacher-owned fixture on a separate route."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Annotated, cast

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel


class NoteInput(BaseModel):
    text: str


class NoteStore:
    def __init__(self) -> None:
        self.notes: list[dict[str, int | str]] = []

    def add(self, text: str) -> dict[str, int | str]:
        note: dict[str, int | str] = {"id": len(self.notes) + 1, "text": text}
        self.notes.append(note)
        return note


def get_store(request: Request) -> NoteStore:
    return cast(NoteStore, request.app.state.store)


def create_app(events: list[str]) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        events.append("startup")
        try:
            yield
        finally:
            events.append("shutdown")

    app = FastAPI(lifespan=lifespan)
    app.state.store = NoteStore()

    @app.post("/shelf-notes", status_code=201)
    def add_note(
        note: NoteInput, store: Annotated[NoteStore, Depends(get_store)]
    ) -> dict[str, int | str]:
        return store.add(note.text)

    @app.get("/shelf-notes")
    def list_notes(store: Annotated[NoteStore, Depends(get_store)]) -> list[dict[str, int | str]]:
        return store.notes

    return app


@dataclass
class ClientCase:
    app: FastAPI
    store: NoteStore
    client: TestClient
    events: list[str]


@contextmanager
def client_scope() -> Iterator[ClientCase]:
    events = ["setup"]
    app = create_app(events)
    store = NoteStore()
    app.dependency_overrides[get_store] = lambda: store
    client = TestClient(app)
    try:
        with client:
            yield ClientCase(app, store, client, events)
    finally:
        try:
            client.close()
        finally:
            app.dependency_overrides.clear()
            events.append("teardown")


@pytest.fixture
def shelf_client() -> Iterator[ClientCase]:
    with client_scope() as case:
        yield case


def main() -> None:
    with client_scope() as first:
        response = first.client.post("/shelf-notes", json={"text": "Read chapter 2"})
        print(f"created: {response.status_code} {response.json()}")
        print(f"during: {first.events}")
    print(f"after: {first.events}; overrides={first.app.dependency_overrides}")
    try:
        with client_scope() as failed:
            raise ValueError("deliberate body failure")
    except ValueError as error:
        print(f"caught: {error}")
    print(f"after failure: {failed.events}; overrides={failed.app.dependency_overrides}")
    with client_scope() as second:
        print(f"fresh notes: {second.client.get('/shelf-notes').json()}")


if __name__ == "__main__":
    main()
