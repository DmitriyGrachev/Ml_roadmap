"""Small, explicit learning routes over the existing curriculum catalog."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from roadmap_tools.catalog import Catalog, CatalogError


class TrackError(ValueError):
    """A route names missing, ambiguous or unowned learning material."""


@dataclass(frozen=True)
class LearningTrack:
    identifier: str
    title: str
    required: tuple[str, ...]
    review: Path


def _text(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TrackError(f"Track {key} must be nonempty text")
    return value


def load_tracks(root: Path, catalog: Catalog | None = None) -> dict[str, LearningTrack]:
    """Validate route IDs and the human assessment document without marking progress."""
    root = root.resolve()
    catalog = Catalog.load(root) if catalog is None else catalog
    try:
        with (root / "learning_tracks.toml").open("rb") as source:
            records = tomllib.load(source).get("tracks")
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise TrackError(f"Cannot read learning_tracks.toml: {exc}") from exc
    if not isinstance(records, list) or not records:
        raise TrackError("tracks must be a nonempty array")
    result = {}
    for record in records:
        if not isinstance(record, dict):
            raise TrackError("Each track must be a table")
        identifier = _text(record, "id")
        if identifier in result:
            raise TrackError(f"Duplicate track: {identifier}")
        title = _text(record, "title")
        required = record.get("required")
        if not isinstance(required, list) or not required:
            raise TrackError(f"Track {identifier}: required must be nonempty")
        identifiers = []
        for item in required:
            if not isinstance(item, str) or not item:
                raise TrackError(f"Track {identifier}: invalid required item")
            if item in identifiers:
                raise TrackError(f"Track {identifier}: duplicate item {item}")
            try:
                catalog.get(item)
            except CatalogError as exc:
                raise TrackError(f"Track {identifier}: unknown catalog ID {item}") from exc
            identifiers.append(item)
        review_text = _text(record, "review")
        review_path = Path(review_text)
        review = (root / review_path).resolve()
        if (
            review_path.is_absolute()
            or PureWindowsPath(review_text).drive
            or not review.is_relative_to(root)
            or not review.is_file()
        ):
            raise TrackError(f"Track {identifier}: review must name a file inside the checkout")
        result[identifier] = LearningTrack(identifier, title, tuple(identifiers), review)
    return result


def unique_test_targets(catalog: Catalog, track: LearningTrack) -> tuple[Path, ...]:
    """Run the union of the declared scopes once, including nested targets only once."""
    paths = list(dict.fromkeys(path for key in track.required for path in catalog.get(key).tests))
    return tuple(
        path
        for path in paths
        if not any(
            other != path and other.is_dir() and path.is_relative_to(other) for other in paths
        )
    )
