"""Validated curriculum catalog loading and lookup."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from types import MappingProxyType
from typing import Literal, cast

CatalogKind = Literal["lesson", "exercise", "project"]
_CATALOG_KINDS: frozenset[str] = frozenset({"lesson", "exercise", "project"})


class CatalogError(ValueError):
    """Describe a curriculum catalog validation failure."""

    def __init__(self, identifier: str, field: str, detail: str) -> None:
        self.identifier = identifier
        self.field = field
        super().__init__(f"Catalog item {identifier!r} has invalid {field}: {detail}")


@dataclass(frozen=True)
class CatalogItem:
    """A validated curriculum item and its repository-owned files."""

    identifier: str
    title: str
    kind: CatalogKind
    readme: Path
    tests: tuple[Path, ...]


@dataclass(frozen=True)
class Catalog:
    """An immutable collection of validated curriculum items."""

    _items_by_identifier: Mapping[str, CatalogItem]

    @classmethod
    def load(cls, repository_root: Path, catalog_path: Path | None = None) -> Catalog:
        """Load and validate a curriculum catalog relative to *repository_root*."""
        root = repository_root.resolve()
        source = _resolve_catalog_path(root, catalog_path)

        try:
            with source.open("rb") as catalog_file:
                document = tomllib.load(catalog_file)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise CatalogError("<catalog>", "catalog_path", str(exc)) from exc

        records = document.get("items")
        if not isinstance(records, list):
            raise CatalogError("<catalog>", "items", "expected an array of item records")

        items: dict[str, CatalogItem] = {}
        for record in records:
            item = _parse_item(record, root)
            if item.identifier in items:
                raise CatalogError(item.identifier, "id", "duplicate identifier")
            items[item.identifier] = item

        return cls(MappingProxyType(items))

    def get(self, identifier: str) -> CatalogItem:
        """Return the item identified by *identifier*."""
        try:
            return self._items_by_identifier[identifier]
        except KeyError as exc:
            raise CatalogError(identifier, "id", "unknown identifier") from exc

    def suggest(self, identifier: str) -> tuple[str, ...]:
        """Return up to three close curriculum identifier matches."""
        return tuple(get_close_matches(identifier, self._items_by_identifier.keys(), n=3))


def _parse_item(record: object, repository_root: Path) -> CatalogItem:
    if not isinstance(record, dict):
        raise CatalogError("<unknown>", "items", "expected a table")

    identifier = _required_string(record, "id", "<unknown>")
    title = _required_string(record, "title", identifier)
    kind = _required_string(record, "kind", identifier)
    if kind not in _CATALOG_KINDS:
        raise CatalogError(identifier, "kind", f"unknown kind {kind!r}")

    readme_value = _required_string(record, "readme", identifier)
    readme = _resolve_path(repository_root, identifier, "readme", readme_value)
    tests = _parse_tests(record, repository_root, identifier)

    return CatalogItem(
        identifier=identifier,
        title=title,
        kind=cast(CatalogKind, kind),
        readme=readme,
        tests=tests,
    )


def _required_string(record: dict[object, object], field: str, identifier: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise CatalogError(identifier, field, "expected a non-empty string")
    return value


def _parse_tests(
    record: dict[object, object], repository_root: Path, identifier: str
) -> tuple[Path, ...]:
    values = record.get("tests")
    if not isinstance(values, list) or not values:
        raise CatalogError(identifier, "tests", "expected a non-empty array of paths")

    paths: list[Path] = []
    for value in values:
        if not isinstance(value, str) or not value:
            raise CatalogError(identifier, "tests", "expected non-empty string paths")
        paths.append(_resolve_path(repository_root, identifier, "tests", value))
    return tuple(paths)


def _resolve_path(repository_root: Path, identifier: str, field: str, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise CatalogError(identifier, field, f"path must be relative: {value!r}")

    resolved_path = (repository_root / path).resolve()
    if not resolved_path.is_relative_to(repository_root):
        raise CatalogError(identifier, field, f"path escapes repository root: {value!r}")
    if not resolved_path.exists():
        raise CatalogError(identifier, field, f"path does not exist: {value!r}")
    return resolved_path


def _resolve_catalog_path(repository_root: Path, catalog_path: Path | None) -> Path:
    path = Path("curriculum.toml") if catalog_path is None else catalog_path
    resolved_path = (path if path.is_absolute() else repository_root / path).resolve()
    if not resolved_path.is_relative_to(repository_root):
        raise CatalogError("<catalog>", "catalog_path", "path escapes repository root")
    return resolved_path
