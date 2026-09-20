"""Intentionally broken mutable-default example."""


def append_audit_tag(
    tag: str,
    tags: list[str] = [],  # noqa: B006 - intentional debugging fixture
) -> list[str]:
    """Append an audit tag while accidentally retaining default state."""
    tags.append(tag)
    return tags
