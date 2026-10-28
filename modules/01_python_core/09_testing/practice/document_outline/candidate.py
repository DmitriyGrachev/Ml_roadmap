"""Intentionally defective AI-review candidate, never the usable implementation."""


def extract_outline(
    text: str,
    *,
    unique: bool = False,
    titles: list[str] = [],  # noqa: B006 - review fixture
) -> tuple[str, ...]:
    """A plausible-looking candidate that does not satisfy the practice contract."""
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            titles.append(line.lstrip(" #"))
    if unique:
        return tuple(set(titles))
    return tuple(titles)
