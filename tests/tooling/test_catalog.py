from __future__ import annotations

from pathlib import Path

import pytest

from roadmap_tools.catalog import Catalog, CatalogError, CatalogItem

VALID_ITEM = """
[[items]]
id = "python-collections"
title = "Collections"
kind = "lesson"
readme = "modules/01_python_core/02_collections/README.md"
tests = ["modules/01_python_core/02_collections"]
"""


def write_catalog(root: Path, body: str) -> None:
    (root / "curriculum.toml").write_text(body, encoding="utf-8")


def make_valid_module(root: Path) -> None:
    module = root / "modules" / "01_python_core" / "02_collections"
    module.mkdir(parents=True)
    (module / "README.md").write_text("# Collections\n", encoding="utf-8")


def test_load_returns_immutable_resolved_catalog_item(tmp_path: Path) -> None:
    make_valid_module(tmp_path)
    write_catalog(tmp_path, VALID_ITEM)

    catalog = Catalog.load(tmp_path)

    item = catalog.get("python-collections")
    assert item == CatalogItem(
        identifier="python-collections",
        title="Collections",
        kind="lesson",
        readme=(tmp_path / "modules/01_python_core/02_collections/README.md").resolve(),
        tests=((tmp_path / "modules/01_python_core/02_collections").resolve(),),
    )
    with pytest.raises(AttributeError):
        item.title = "Changed"  # type: ignore[misc]


def test_load_rejects_duplicate_identifier_with_identifier_field(tmp_path: Path) -> None:
    make_valid_module(tmp_path)
    write_catalog(tmp_path, VALID_ITEM + VALID_ITEM)

    with pytest.raises(CatalogError) as raised:
        Catalog.load(tmp_path)

    assert raised.value.identifier == "python-collections"
    assert raised.value.field == "id"


@pytest.mark.parametrize(
    ("body", "identifier", "field"),
    [
        (
            """
[[items]]
id = "python-collections"
title = "Collections"
kind = "article"
readme = "modules/01_python_core/02_collections/README.md"
tests = ["modules/01_python_core/02_collections"]
""",
            "python-collections",
            "kind",
        ),
        (
            """
[[items]]
id = "python-collections"
title = "Collections"
kind = "lesson"
readme = "modules/01_python_core/02_collections/README.md"
tests = []
""",
            "python-collections",
            "tests",
        ),
        (
            """
[[items]]
id = "python-collections"
kind = "lesson"
readme = "modules/01_python_core/02_collections/README.md"
tests = ["modules/01_python_core/02_collections"]
""",
            "python-collections",
            "title",
        ),
    ],
)
def test_load_rejects_malformed_item_with_offending_field(
    tmp_path: Path, body: str, identifier: str, field: str
) -> None:
    make_valid_module(tmp_path)
    write_catalog(tmp_path, body)

    with pytest.raises(CatalogError) as raised:
        Catalog.load(tmp_path)

    assert raised.value.identifier == identifier
    assert raised.value.field == field


@pytest.mark.parametrize(
    ("field", "body"),
    [
        (
            "readme",
            VALID_ITEM.replace(
                "modules/01_python_core/02_collections/README.md", "missing/README.md"
            ),
        ),
        (
            "tests",
            VALID_ITEM.replace(
                'tests = ["modules/01_python_core/02_collections"]',
                'tests = ["missing/tests"]',
            ),
        ),
    ],
)
def test_load_rejects_missing_catalog_path(tmp_path: Path, field: str, body: str) -> None:
    make_valid_module(tmp_path)
    write_catalog(tmp_path, body)

    with pytest.raises(CatalogError) as raised:
        Catalog.load(tmp_path)

    assert raised.value.identifier == "python-collections"
    assert raised.value.field == field


@pytest.mark.parametrize(
    ("field", "body"),
    [
        (
            "readme",
            VALID_ITEM.replace(
                "modules/01_python_core/02_collections/README.md", "../outside/README.md"
            ),
        ),
        (
            "tests",
            VALID_ITEM.replace(
                'tests = ["modules/01_python_core/02_collections"]',
                'tests = ["../outside"]',
            ),
        ),
    ],
)
def test_load_rejects_path_escaping_repository_root(tmp_path: Path, field: str, body: str) -> None:
    make_valid_module(tmp_path)
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    (outside / "README.md").write_text("outside", encoding="utf-8")
    write_catalog(tmp_path, body)

    with pytest.raises(CatalogError) as raised:
        Catalog.load(tmp_path)

    assert raised.value.identifier == "python-collections"
    assert raised.value.field == field


def test_get_rejects_unknown_identifier_with_identifier_field(tmp_path: Path) -> None:
    make_valid_module(tmp_path)
    write_catalog(tmp_path, VALID_ITEM)

    with pytest.raises(CatalogError) as raised:
        Catalog.load(tmp_path).get("python-collectons")

    assert raised.value.identifier == "python-collectons"
    assert raised.value.field == "id"


def test_suggest_returns_close_catalog_identifiers(tmp_path: Path) -> None:
    make_valid_module(tmp_path)
    write_catalog(tmp_path, VALID_ITEM)

    assert Catalog.load(tmp_path).suggest("python-collectons") == ("python-collections",)
