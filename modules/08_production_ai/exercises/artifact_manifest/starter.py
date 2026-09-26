"""Check portable manifest keys and hashes of supplied local byte snapshots."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactEntry:
    path: str
    sha256: str


@dataclass(frozen=True)
class ArtifactManifest:
    schema_version: int
    release_id: str
    entries: tuple[ArtifactEntry, ...]


def validate_manifest(
    manifest: ArtifactManifest, snapshots: Mapping[str, bytes]
) -> tuple[str, ...]:
    """Validate metadata and matching content; return sorted artifact paths."""
    # TODO: Validate every manifest field before checking presence and SHA-256.
    raise NotImplementedError("Implement library artifact manifest validation")
