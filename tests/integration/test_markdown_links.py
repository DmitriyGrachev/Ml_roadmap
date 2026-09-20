"""Repository-wide local Markdown link contracts."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INLINE_LINK = re.compile(
    r"!?\[(?P<label>[^]\n]*)\]\(\s*(?:<(?P<angled>[^>\n]+)>|(?P<plain>[^\s)]+))"
)
FENCE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")
EXAMPLE_PLACEHOLDERS = frozenset(
    {"path/to/file.md", "path/to/readme.md", "relative/path/to/file.md", "example/path.md"}
)


@dataclass(frozen=True)
class BrokenLink:
    """A local Markdown target that cannot be resolved safely."""

    source: Path
    label: str
    target: str


def tracked_markdown_files(repository_root: Path) -> tuple[Path, ...]:
    """Return only Markdown files tracked by Git."""

    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        repository_root / relative
        for relative in result.stdout.split("\0")
        if relative.casefold().endswith(".md")
    )


def without_fenced_code(markdown: str) -> str:
    """Remove fenced code while preserving ordinary Markdown lines."""

    visible: list[str] = []
    active_marker: str | None = None
    active_length = 0
    for line in markdown.splitlines():
        match = FENCE.match(line)
        if active_marker is None and match is not None:
            fence = match.group("fence")
            active_marker, active_length = fence[0], len(fence)
            continue
        if active_marker is not None:
            stripped = line.lstrip()
            if stripped.startswith(active_marker * active_length):
                active_marker = None
            continue
        visible.append(line)
    return "\n".join(visible)


def local_links(markdown: str) -> tuple[tuple[str, str], ...]:
    """Extract labels and targets for local, non-placeholder inline links."""

    links: list[tuple[str, str]] = []
    for match in INLINE_LINK.finditer(without_fenced_code(markdown)):
        label = match.group("label")
        target = (match.group("angled") or match.group("plain")).strip()
        lower = target.casefold()
        windows_drive = re.match(r"^[a-z]:", target, re.IGNORECASE)
        has_scheme = re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE)
        if (
            target.startswith(("#", "//"))
            or (has_scheme is not None and windows_drive is None)
            or lower in EXAMPLE_PLACEHOLDERS
            or "{placeholder}" in lower
        ):
            continue
        links.append((label, target))
    return tuple(links)


def broken_local_links(document: Path, repository_root: Path) -> tuple[BrokenLink, ...]:
    """Resolve one document's local links with both slash styles."""

    issues: list[BrokenLink] = []
    for label, target in local_links(document.read_text(encoding="utf-8")):
        path_text = unquote(target.split("#", 1)[0].split("?", 1)[0]).replace("\\", "/")
        windows_path = PureWindowsPath(path_text)
        if windows_path.drive or windows_path.root:
            issues.append(BrokenLink(document, label, target))
            continue
        resolved = (document.parent / path_text).resolve()
        if not resolved.is_relative_to(repository_root.resolve()) or not resolved.exists():
            issues.append(BrokenLink(document, label, target))
    return tuple(issues)


def test_every_tracked_local_markdown_link_resolves() -> None:
    issues = tuple(
        issue
        for document in tracked_markdown_files(REPOSITORY_ROOT)
        for issue in broken_local_links(document, REPOSITORY_ROOT)
    )

    assert issues == ()


def test_link_checker_is_windows_safe_and_ignores_only_explicit_nonlocal_targets(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository with spaces"
    document = root / "docs" / "guide.md"
    target = root / "docs" / "target folder" / "README.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Target\n", encoding="utf-8")
    document.write_text(
        "\n".join(
            (
                r"[Windows path](target%20folder\README.md)",
                "[anchor](#section)",
                "[external](https://example.invalid/missing.md)",
                "[placeholder](path/to/file.md)",
                "```markdown",
                "[fenced](missing.md)",
                "```",
            )
        ),
        encoding="utf-8",
    )

    assert broken_local_links(document, root) == ()
    document.write_text("[Broken](missing\\README.md)\n", encoding="utf-8")
    issues = broken_local_links(document, root)
    assert len(issues) == 1
    assert issues[0].source == document
    assert issues[0].label == "Broken"
    assert issues[0].target == "missing\\README.md"


def test_link_checker_rejects_windows_drive_relative_targets(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    document = root / "docs" / "guide.md"
    document.parent.mkdir(parents=True)
    document.write_text(
        "[Ambiguous drive path](C:README.md)\n",
        encoding="utf-8",
    )

    assert local_links(document.read_text(encoding="utf-8")) == (
        ("Ambiguous drive path", "C:README.md"),
    )
    assert broken_local_links(document, root) == (
        BrokenLink(document, "Ambiguous drive path", "C:README.md"),
    )
