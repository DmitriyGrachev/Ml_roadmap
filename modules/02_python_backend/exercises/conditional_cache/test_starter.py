"""A conditional request changes status and body, but preserves the representation tag."""

import pytest
from fastapi.testclient import TestClient

from roadmap_tools.exercise import exercise_call

from .starter import create_app

pytestmark = pytest.mark.student_exercise
ABC_TAG = '"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"'


def test_document_is_plain_text_with_sha256_etag() -> None:
    with TestClient(exercise_call(create_app, "abc")) as client:
        response = client.get("/document")
    assert response.status_code == 200
    assert response.text == "abc"
    assert response.headers["etag"] == ABC_TAG
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.parametrize(
    "condition", [ABC_TAG, f"W/{ABC_TAG}", "*", f'"old", {ABC_TAG}', f"  {ABC_TAG}  "]
)
def test_matching_conditions_return_empty_304(condition: str) -> None:
    with TestClient(exercise_call(create_app, "abc")) as client:
        response = client.get("/document", headers={"If-None-Match": condition})
    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == ABC_TAG


@pytest.mark.parametrize(
    "condition", ['"different"', ABC_TAG[1:-1], ABC_TAG.upper(), '"old", W/"other"']
)
def test_nonmatching_condition_returns_document(condition: str) -> None:
    with TestClient(exercise_call(create_app, "abc")) as client:
        response = client.get("/document", headers={"If-None-Match": condition})
    assert response.status_code == 200
    assert response.text == "abc"
    assert response.headers["etag"] == ABC_TAG


def test_empty_document_is_a_valid_representation() -> None:
    with TestClient(exercise_call(create_app, "")) as client:
        response = client.get("/document")
    assert response.status_code == 200
    assert response.content == b""
    assert (
        response.headers["etag"]
        == '"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"'
    )


def test_unicode_and_app_isolation_and_repeatability() -> None:
    with (
        TestClient(exercise_call(create_app, "ploaie 🌧")) as first,
        TestClient(exercise_call(create_app, "abc")) as second,
    ):
        response = first.get("/document")
        assert response.content == "ploaie 🌧".encode()
        assert first.get("/document").headers["etag"] == response.headers["etag"]
        assert second.get("/document").headers["etag"] == ABC_TAG
        assert response.headers["etag"] != ABC_TAG
