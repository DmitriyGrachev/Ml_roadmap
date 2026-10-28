"""Load one operator-selected immutable bundle during ASGI lifespan."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..artifacts import LocalClassifier, load_trusted_local_classifier, predict_documents, read_json
from ..contracts import object_value, sha256_value


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value


class PredictionResponse(BaseModel):
    predicted_label: str
    bundle_sha256: str
    model_id: str
    preprocessing_version: int


def create_app(
    bundle_root: Path,
    expected_manifest_sha256: str,
    *,
    trusted_local_artifact: bool = False,
) -> FastAPI:
    """No I/O at construction; validate/load once per successful startup.

    An operator-protected path/digest expresses selection. The separate trust flag
    permits executable local sklearn serialization; it is never request input.
    """
    sha256_value(expected_manifest_sha256, "expected_manifest_sha256")
    if bundle_root.as_posix().startswith("//"):
        raise ValueError("bundle_root must be a local path, not a network share")

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        classifier = load_trusted_local_classifier(
            bundle_root,
            expected_manifest_sha256,
            trusted_local_artifact=trusted_local_artifact,
        )
        # Loader replays the frozen test cohort; this is mechanical readiness only.
        application.state.classifier = classifier
        try:
            yield
        finally:
            application.state.classifier = None

    app = FastAPI(title="Document CPU teacher service", lifespan=lifespan)
    app.state.classifier = None

    @app.get("/ready")
    def ready() -> JSONResponse:
        classifier: LocalClassifier | None = app.state.classifier
        if classifier is None:
            return JSONResponse({"ready": False}, status_code=503)
        return JSONResponse({"ready": True, "bundle_sha256": classifier.bundle.manifest_sha256})

    @app.post("/predict", response_model=PredictionResponse)
    def predict(request: PredictionRequest) -> PredictionResponse:
        classifier: LocalClassifier | None = app.state.classifier
        if classifier is None:
            raise HTTPException(status_code=503, detail="bundle is not ready")
        manifest = classifier.bundle.manifest
        return PredictionResponse(
            predicted_label=predict_documents(classifier, [request.text])[0],
            bundle_sha256=classifier.bundle.manifest_sha256,
            model_id=manifest["model"]["id"],
            preprocessing_version=manifest["preprocessing"]["version"],
        )

    return app


def create_app_from_config(config_path: Path, *, trusted_local_artifact: bool = False) -> FastAPI:
    """Read an exact operator JSON config; startup still owns bundle loading."""
    config = object_value(read_json(config_path), "service config")
    if set(config) != {"bundle_root", "expected_manifest_sha256"}:
        raise ValueError("service config requires exactly bundle_root and expected_manifest_sha256")
    if not isinstance(config["bundle_root"], str):
        raise ValueError("bundle_root must be an absolute local path")
    root = Path(config["bundle_root"])
    if not root.is_absolute() or root.as_posix().startswith("//"):
        raise ValueError("bundle_root must be an absolute local path")
    return create_app(
        root,
        config["expected_manifest_sha256"],
        trusted_local_artifact=trusted_local_artifact,
    )


def factory() -> FastAPI:
    """Uvicorn --factory entry point for safe JSON rules, including the container."""
    config = os.environ.get("ROADMAP_SERVICE_CONFIG")
    if not config:
        raise ValueError("ROADMAP_SERVICE_CONFIG must name the operator JSON config")
    return create_app_from_config(Path(config))
