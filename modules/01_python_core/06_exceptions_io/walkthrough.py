"""Separate failure phases; deliberately not a general JSON exporter."""

import json
import tempfile
from pathlib import Path


def cleanup_owned(draft: Path, original: BaseException) -> None:
    """A failed cleanup is evidence on the original error, not a replacement error."""
    try:
        draft.unlink(missing_ok=True)
    except OSError as cleanup_error:
        original.add_note(f"cleanup failed for {draft}: {cleanup_error}")


def serialize_broken_catalog(directory: Path) -> None:
    """Observe partial serialization in an owned draft; never publish this catalog."""
    draft: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix="catalog-",
            suffix=".tmp",
            delete=False,
        ) as writer:
            draft = Path(writer.name)
            json.dump({"shelf": "north", "colors": {"blue"}}, writer)
    except BaseException as error:
        # Catch for resource cleanup only. The bare raise preserves the original failure.
        if draft is not None:
            cleanup_owned(draft, error)
        raise


def publish_notice(destination: Path) -> None:
    """Publish one fixed plain-text notice; no payload or serialization interface."""
    draft: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix="notice-",
            suffix=".tmp",
            delete=False,
        ) as writer:
            draft = Path(writer.name)
            writer.write("Library closes at 18:00.\n")
        # The context is finished: the writer is closed before replacement on Windows.
        draft.replace(destination)
    except BaseException as error:
        if draft is not None:
            cleanup_owned(draft, error)
        raise


def main() -> None:
    with tempfile.TemporaryDirectory() as directory_name:
        directory = Path(directory_name)
        notice = directory / "notice.txt"
        notice.write_text("old notice", encoding="utf-8")
        publish_notice(notice)
        print(f"success: {notice.read_text(encoding='utf-8').strip()}")

        catalog = directory / "catalog.json"
        catalog.write_bytes(b"old catalog")
        try:
            serialize_broken_catalog(directory)
        except TypeError as error:
            print(f"serialization: {type(error).__name__}; old={catalog.read_bytes()!r}")

        # A nonempty directory is an actual incompatible replacement target on Windows/POSIX.
        blocked = directory / "occupied"
        blocked.mkdir()
        sentinel = blocked / "keep.txt"
        sentinel.write_bytes(b"other owner")
        try:
            publish_notice(blocked)
        except OSError:
            print(f"replacement: failed; unrelated={sentinel.read_bytes()!r}")
        print(f"drafts remaining: {len(list(directory.glob('*.tmp')))}")


if __name__ == "__main__":
    main()
