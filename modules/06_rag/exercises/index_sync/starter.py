"""Student boundary for comparing source and indexed revision snapshots."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Revision:
    """A document ID and an opaque revision token."""

    document_id: str
    revision: str


@dataclass(frozen=True)
class SyncPlan:
    """A deterministic change plan; no files or index are modified."""

    create: tuple[Revision, ...]
    update: tuple[Revision, ...]
    delete: tuple[str, ...]
    unchanged: tuple[str, ...]


def plan_index_sync(source: tuple[Revision, ...], indexed: tuple[Revision, ...]) -> SyncPlan:
    """Compare exact revision tokens and return sorted change groups."""
    for snapshot in (source, indexed):
        ids: set[str] = set()
        for item in snapshot:
            if not isinstance(item.document_id, str) or not item.document_id.strip():
                raise ValueError("document IDs must be nonblank strings")
            if not isinstance(item.revision, str) or not item.revision.strip():
                raise ValueError("revision tokens must be nonblank strings")
            if item.document_id in ids:
                raise ValueError("document IDs must be unique within each snapshot")
            ids.add(item.document_id)
    # TODO: classify IDs and return source revisions for creates and updates.
    raise NotImplementedError("plan a library index refresh")
