"""Behavioral contracts for the repository's shared learning documentation."""

from __future__ import annotations

import re
from pathlib import Path

from roadmap_tools.catalog import Catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROOT_README = REPOSITORY_ROOT / "README.md"
PROGRESS_PATH = REPOSITORY_ROOT / "progress.md"
SHARED_DOCUMENTS = (
    ROOT_README,
    REPOSITORY_ROOT / "docs" / "roadmap.md",
    REPOSITORY_ROOT / "docs" / "setup.md",
    REPOSITORY_ROOT / "docs" / "learning-rules.md",
    REPOSITORY_ROOT / "docs" / "testing-exercises.md",
    REPOSITORY_ROOT / "docs" / "java-to-python-cheatsheet.md",
)
REQUIRED_COMMANDS = (
    "uv sync --all-groups",
    "uv run python scripts/learn.py validate-env",
    "uv run python scripts/learn.py list",
    "uv run python scripts/learn.py status",
    "uv run python scripts/learn.py test python-collections",
    "uv run pytest",
    "uv run pytest modules/01_python_core",
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run mypy",
)
PLANNED_LESSON_IDS = (
    "python-environment",
    "python-object-model",
    "python-collections",
    "python-functions",
    "python-typing",
    "python-data-modeling",
    "python-io",
    "python-generators",
    "python-decorators",
    "python-testing",
    "python-asyncio",
    "backend-fastapi",
    "backend-pydantic",
    "backend-architecture",
    "backend-config-errors",
    "backend-async",
    "backend-sqlalchemy",
    "backend-postgresql",
    "backend-testing",
    "backend-docker",
    "data-numpy",
    "data-pandas",
    "data-quality",
    "data-statistics",
    "data-splits",
    "data-fraud-metrics",
)
FUTURE_MODULES = (
    "04_machine_learning",
    "05_llm_engineering",
    "06_rag",
    "07_agents",
    "08_production_ai",
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
FENCED_CODE_BLOCK = re.compile(r"^```[^\n]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
CHECKLIST_ENTRY = re.compile(r"^- \[[ ~x]\] ([a-z0-9-]+)$", re.MULTILINE)


def test_root_readme_exposes_every_learning_command() -> None:
    """A supported command must stay discoverable as an executable command line."""
    readme = ROOT_README.read_text(encoding="utf-8")
    fenced_commands = _fenced_command_lines(readme)

    for command in REQUIRED_COMMANDS:
        assert command in fenced_commands


def test_fenced_command_lines_ignore_inline_command_mentions() -> None:
    """Narrative mentions of a command cannot satisfy the executable-command contract."""
    document = (
        "Use `uv run pytest` for repository health.\n\n"
        "```powershell\n"
        "  uv run ruff check .  \n"
        "```\n"
    )

    assert _fenced_command_lines(document) == ("uv run ruff check .",)


def test_shared_documentation_relative_links_resolve() -> None:
    """A learner can follow every local shared-documentation link."""
    unresolved: list[str] = []
    for document in SHARED_DOCUMENTS:
        for target in _relative_markdown_targets(document):
            destination = (document.parent / target).resolve()
            if not destination.exists():
                unresolved.append(f"{document.relative_to(REPOSITORY_ROOT)} -> {target}")

    assert not unresolved, "Unresolved local Markdown links:\n" + "\n".join(unresolved)


def test_progress_is_an_ordered_editable_module_01_to_03_checklist() -> None:
    """Learners can update the planned lesson sequence before it is implemented."""
    entries = CHECKLIST_ENTRY.findall(PROGRESS_PATH.read_text(encoding="utf-8"))

    assert entries == list(PLANNED_LESSON_IDS)


def test_progress_includes_every_loaded_catalog_lesson() -> None:
    """A catalog lesson cannot be released without a progress entry."""
    entries = set(CHECKLIST_ENTRY.findall(PROGRESS_PATH.read_text(encoding="utf-8")))
    lesson_ids = {
        item.identifier for item in Catalog.load(REPOSITORY_ROOT).items if item.kind == "lesson"
    }

    assert lesson_ids <= entries


def test_future_module_placeholders_describe_deferred_learning() -> None:
    """Future modules remain useful roadmap entries without implying exercises exist."""
    for module in FUTURE_MODULES:
        readme = (REPOSITORY_ROOT / "modules" / module / "README.md").read_text(encoding="utf-8")
        assert "## Scope" in readme
        assert "## Prerequisites" in readme
        assert "## Planned outcomes" in readme
        assert "Exercises are intentionally deferred." in readme


def _relative_markdown_targets(document: Path) -> tuple[Path, ...]:
    """Return local Markdown destinations while excluding anchors and external links."""
    targets: list[Path] = []
    for raw_target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
        target = raw_target.split(maxsplit=1)[0].split("#", maxsplit=1)[0]
        if target and "://" not in target and not target.startswith(("#", "/", "mailto:")):
            targets.append(Path(target))
    return tuple(targets)


def _fenced_command_lines(document: str) -> tuple[str, ...]:
    """Return non-empty, stripped lines from Markdown fenced code blocks."""
    return tuple(
        line.strip()
        for block in FENCED_CODE_BLOCK.findall(document)
        for line in block.splitlines()
        if line.strip()
    )
