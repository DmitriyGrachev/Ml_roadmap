"""A local service lifecycle; TestClient does not start a public server."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field


@dataclass
class Lifecycle:
    ready: bool = False
    closed: bool = False

    def drain(self) -> None:
        self.ready = False


class LabelRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    item_id: str = Field(pattern=r"^M-[0-9]{3}$")


class LabelResponse(BaseModel):
    item_id: str
    label: str
    release: str


def create_app(lifecycle: Lifecycle) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        lifecycle.closed = False
        lifecycle.ready = True
        try:
            yield
        finally:
            lifecycle.ready = False
            lifecycle.closed = True

    app = FastAPI(lifespan=lifespan)

    @app.get("/live")
    def live() -> dict[str, bool]:
        return {"alive": True}

    @app.get("/ready")
    def ready() -> dict[str, bool]:
        if not lifecycle.ready:
            raise HTTPException(503, "service is not accepting work")
        return {"ready": True}

    @app.post("/labels", response_model=LabelResponse)
    def label(request: LabelRequest) -> LabelResponse:
        if not lifecycle.ready:
            raise HTTPException(503, "service is draining")
        return LabelResponse(item_id=request.item_id, label="Museum catalog fixture", release="v1")

    return app


def main() -> None:
    lifecycle = Lifecycle()
    with TestClient(create_app(lifecycle)) as client:
        print(client.post("/labels", json={"item_id": "M-001"}).json())
        lifecycle.drain()
        print({"live": client.get("/live").status_code, "ready": client.get("/ready").status_code})
    print({"closed": lifecycle.closed})


if __name__ == "__main__":
    main()
