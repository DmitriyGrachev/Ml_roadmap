"""Student factory for a static text resource supporting conditional GET."""

from fastapi import FastAPI


def create_app(document: str) -> FastAPI:
    """Serve GET /document with a content-derived ETag and If-None-Match handling."""
    # TODO: hash UTF-8 content, parse validators, and return a 200 or empty 304 response.
    raise NotImplementedError("serve a conditional document")
