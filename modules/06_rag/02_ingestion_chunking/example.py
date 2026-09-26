"""Plan a deterministic incremental update over local source fingerprints."""

import hashlib
from collections.abc import Mapping


def source_digest(text: str, policy: str = "plain-text-v1") -> str:
    return hashlib.sha256(f"{policy}\0{text}".encode()).hexdigest()


def update_plan(
    previous: Mapping[str, str], current: Mapping[str, str]
) -> dict[str, tuple[str, ...]]:
    """Compare source digests, not chunk windows or embedding vectors."""
    return {
        "unchanged": tuple(sorted(key for key in current if previous.get(key) == current[key])),
        "replace": tuple(sorted(key for key in current if previous.get(key) != current[key])),
        "tombstone": tuple(sorted(set(previous) - set(current))),
    }


def main() -> None:
    previous = {"roses": source_digest("Water weekly."), "closed-bed": source_digest("Archived.")}
    current = {"roses": source_digest("Water twice weekly."), "herbs": source_digest("Use shade.")}
    print(update_plan(previous, current))


if __name__ == "__main__":
    main()
