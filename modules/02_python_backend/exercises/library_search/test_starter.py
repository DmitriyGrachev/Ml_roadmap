"""API contract checks for the library search exercise."""

from typing import cast

import pytest
from fastapi.testclient import TestClient

from roadmap_tools.exercise import exercise_call

from .starter import Book, create_app


@pytest.fixture
def books() -> list[Book]:
    return [
        Book("b3", "Wild Gardens", "A. Reed", 2021, False),
        Book("b1", "Atlas", "B. Lake", 2010, True),
        Book("b2", "atlas", "A. Reed", 2010, True),
        Book("b4", "Clouds", "C. Hill", 2023, True),
    ]


@pytest.mark.student_exercise
def test_default_sort_is_casefolded_and_stable_with_documented_shape(books: list[Book]) -> None:
    with TestClient(exercise_call(create_app, books)) as client:
        response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == {
        "total": 4,
        "page": 1,
        "page_size": 10,
        "items": [
            {"id": "b1", "title": "Atlas", "author": "B. Lake", "year": 2010, "available": True},
            {"id": "b2", "title": "atlas", "author": "A. Reed", "year": 2010, "available": True},
            {"id": "b4", "title": "Clouds", "author": "C. Hill", "year": 2023, "available": True},
            {
                "id": "b3",
                "title": "Wild Gardens",
                "author": "A. Reed",
                "year": 2021,
                "available": False,
            },
        ],
    }


@pytest.mark.student_exercise
def test_filtering_precedes_pagination_and_query_searches_author(books: list[Book]) -> None:
    with TestClient(exercise_call(create_app, books)) as client:
        response = client.get("/books", params={"q": "  REED  ", "page_size": 1, "page": 2})
        available = client.get("/books", params={"q": "reed", "available": "true"})
        unavailable = client.get("/books", params={"available": "false"})
        title = client.get("/books", params={"q": "ATLAS"})
    assert response.json()["total"] == 2
    assert [item["id"] for item in response.json()["items"]] == ["b3"]
    assert [item["id"] for item in available.json()["items"]] == ["b2"]
    assert [item["id"] for item in unavailable.json()["items"]] == ["b3"]
    assert title.json()["total"] == 2


@pytest.mark.student_exercise
def test_descending_year_sort_preserves_input_order_for_ties(books: list[Book]) -> None:
    with TestClient(exercise_call(create_app, books)) as client:
        response = client.get("/books", params={"sort": "year", "descending": "true"})
    assert [item["id"] for item in response.json()["items"]] == ["b4", "b3", "b1", "b2"]


@pytest.mark.student_exercise
def test_empty_search_out_of_range_page_and_blank_query(books: list[Book]) -> None:
    with TestClient(exercise_call(create_app, books)) as client:
        assert client.get("/books", params={"q": "missing"}).json()["items"] == []
        beyond = client.get("/books", params={"page": 10}).json()
        assert beyond["items"] == []
        assert beyond["total"] == 4
        assert client.get("/books", params={"q": "  "}).json()["total"] == 4
    with TestClient(exercise_call(create_app, [])) as empty:
        assert empty.get("/books").json() == {"total": 0, "page": 1, "page_size": 10, "items": []}


@pytest.mark.student_exercise
@pytest.mark.parametrize(
    "query",
    [
        "page=0",
        "page=-1",
        "page=x",
        "page_size=0",
        "page_size=51",
        "page_size=1.5",
        "sort=author",
        "available=perhaps",
        "descending=perhaps",
    ],
)
def test_invalid_queries_return_422(books: list[Book], query: str) -> None:
    with TestClient(exercise_call(create_app, books)) as client:
        assert client.get(f"/books?{query}").status_code == 422


@pytest.mark.student_exercise
def test_app_snapshots_catalog_and_calls_do_not_mutate_input(books: list[Book]) -> None:
    before = books.copy()
    app = exercise_call(create_app, books)
    with TestClient(app) as client:
        first = client.get("/books").json()
        assert first == client.get("/books").json()
        assert books == before
        books.clear()
        assert client.get("/books").json() == first
    with TestClient(exercise_call(create_app, [])) as other:
        assert other.get("/books").json()["total"] == 0


@pytest.mark.parametrize(
    "book",
    [
        Book("", "Title", "Author", 2000, True),
        Book("b", " ", "Author", 2000, True),
        Book("b", "Title", "", 2000, True),
        Book("b", "Title", "Author", 0, True),
        Book("b", "Title", "Author", 10000, True),
        Book("b", "Title", "Author", cast(int, True), True),
        Book("b", "Title", "Author", 2000, cast(bool, 1)),
    ],
)
def test_invalid_catalog_entry(book: Book) -> None:
    with pytest.raises(ValueError, match="book"):
        exercise_call(create_app, [book])


def test_duplicate_catalog_ids(books: list[Book]) -> None:
    with pytest.raises(ValueError, match="unique"):
        exercise_call(create_app, [books[0], books[0]])
