"""A local compatibility check for a rollback manifest; no deployment occurs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Release:
    name: str
    readable_schemas: frozenset[int]


def rollback_preflight(previous: Release, stored_schema: int, artifact_available: bool) -> bool:
    return artifact_available and stored_schema in previous.readable_schemas


def main() -> None:
    previous = Release("museum-v1", frozenset({1}))
    print(
        {
            "schema_1_can_restore": rollback_preflight(previous, 1, True),
            "schema_2_can_restore": rollback_preflight(previous, 2, True),
        }
    )
    print("A previous release name alone does not reverse an incompatible data migration.")


if __name__ == "__main__":
    main()
