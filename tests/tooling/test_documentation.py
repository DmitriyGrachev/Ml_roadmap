"""Behavioral contracts for the repository's shared learning documentation."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from roadmap_tools.catalog import Catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROOT_README = REPOSITORY_ROOT / "README.md"
DESIGN_SPEC = (
    REPOSITORY_ROOT / "docs" / "superpowers" / "specs" / "2026-09-19-ai-engineer-roadmap-design.md"
)
TRANSACTION_DOMAIN = (
    REPOSITORY_ROOT / "projects" / "banking_ai_lab" / "banking_ai_lab" / "domain.py"
)
SETUP_GUIDE = REPOSITORY_ROOT / "docs" / "setup.md"
ROADMAP_GUIDE = REPOSITORY_ROOT / "docs" / "roadmap.md"
TESTING_GUIDE = REPOSITORY_ROOT / "docs" / "testing-exercises.md"
SQLALCHEMY_README = (
    REPOSITORY_ROOT / "modules" / "02_python_backend" / "06_sqlalchemy" / "README.md"
)
PROGRESS_PATH = REPOSITORY_ROOT / "progress.md"
SHARED_DOCUMENTS = (
    ROOT_README,
    ROADMAP_GUIDE,
    SETUP_GUIDE,
    REPOSITORY_ROOT / "docs" / "learning-rules.md",
    TESTING_GUIDE,
    REPOSITORY_ROOT / "docs" / "java-to-python-cheatsheet.md",
)
REQUIRED_COMMANDS = (
    "uv sync --locked",
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
    "ml-problem-framing",
    "ml-validation",
    "ml-preprocessing",
    "ml-models",
    "ml-evaluation",
    "ml-reproducibility",
    "llm-interfaces",
    "llm-prompt-contracts",
    "llm-structured-outputs",
    "llm-context-cost",
    "llm-evaluation",
    "llm-reliability-tools",
    "rag-contracts",
    "rag-ingestion",
    "rag-retrieval",
    "rag-hybrid",
    "rag-grounding",
    "rag-evaluation",
    "agents-state",
    "agents-tools",
    "agents-loop",
    "agents-checkpoints",
    "agents-langgraph-mcp",
    "agents-evaluation",
    "production-serving",
    "production-releases",
    "production-observability",
    "production-resilience",
    "production-privacy",
    "production-rollout",
    "ml-training-bridge",
    "lab-pytorch",
    "lab-huggingface",
)
READINESS_IDS = (
    "ml-gradient-derivations",
    "ml-linear-geometry",
    "ml-tree-boosting",
    "data-training-stability",
    "python-async-lifecycle",
    "python-package-delivery",
    "backend-schema-migrations",
    "ml-external-tabular",
    "document-external-model-study",
    "rag-end-to-end-evaluation",
    "production-service-lifecycle",
    "ml-data-pipeline",
)
APPLIED_TOOLS_IDS = (
    "data-vectorized-features",
    "data-point-in-time-features",
    "ml-sklearn-selection",
    "lab-hf-trainer-workflow",
    "lab-token-classification",
    "lab-sft-lora",
    "lab-training-efficiency",
    "rag-neural-reranking",
    "rag-embedding-adaptation",
    "ml-experiment-management",
    "lab-vllm-measurements",
)
FINAL_MODULES = (
    "06_rag",
    "07_agents",
    "08_production_ai",
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
FENCED_CODE_BLOCK = re.compile(r"^```[^\n]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
CHECKLIST_ENTRY = re.compile(r"^- \[[ ~x]\] ([a-z0-9-]+)$", re.MULTILINE)
IMPLEMENTED_MODULE_RANGE = "Modules 01\N{EN DASH}08"
REPOSITORY_STRUCTURE_PATHS = (
    "modules/01_python_core/",
    "modules/02_python_backend/",
    "modules/03_data_foundations/",
    "modules/04_machine_learning/",
    "modules/05_llm_engineering/",
    "modules/06_rag/",
    "modules/07_agents/",
    "modules/08_production_ai/",
    "labs/",
    "projects/banking_ai_lab/",
    "projects/document_intelligence_lab/",
    "datasets/",
    "scripts/",
    "src/roadmap_tools/",
    "tests/integration/",
)


def test_root_readme_exposes_every_learning_command() -> None:
    """A supported command must stay discoverable as an executable command line."""
    readme = ROOT_README.read_text(encoding="utf-8")
    fenced_commands = _fenced_command_lines(readme)

    for command in REQUIRED_COMMANDS:
        assert command in fenced_commands


def test_root_readme_structure_names_existing_repository_boundaries() -> None:
    """The overview tree cannot retain missing paths or omit a major learning boundary."""
    readme = ROOT_README.read_text(encoding="utf-8")
    structure = _markdown_section(readme, "Repository structure")
    documented_paths = tuple(
        match.group(1)
        for match in re.finditer(r"^[|\u251c\u2514]\S*\s+([^ ]+/)\s*$", structure, re.MULTILINE)
    )

    assert documented_paths == REPOSITORY_STRUCTURE_PATHS
    assert all((REPOSITORY_ROOT / path).is_dir() for path in documented_paths)


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


def test_shared_guides_describe_the_implemented_curriculum() -> None:
    root_readme = ROOT_README.read_text(encoding="utf-8")
    setup_guide = SETUP_GUIDE.read_text(encoding="utf-8")
    roadmap_guide = ROADMAP_GUIDE.read_text(encoding="utf-8")
    testing_guide = TESTING_GUIDE.read_text(encoding="utf-8")

    assert f"{IMPLEMENTED_MODULE_RANGE} are implemented" in root_readme
    assert f"{IMPLEMENTED_MODULE_RANGE} are planned next" not in root_readme
    assert "their lesson folders are not present yet" not in root_readme
    assert "These are intentionally inline paths until Module 01 is added" not in setup_guide
    assert "After lessons arrive" not in setup_guide
    assert "The first implemented learning wave covers Modules 01" in roadmap_guide
    assert "will cover Modules 01" not in roadmap_guide
    assert "planned first lesson path" not in roadmap_guide
    assert "Each exercise README names its focused test command" in testing_guide
    assert "README will name" not in testing_guide
    assert "later, `uv run python scripts/learn.py test" not in testing_guide


def test_design_spec_uses_the_canonical_transaction_columns() -> None:
    """The design must describe the domain schema rather than maintain a second loose schema."""
    design = DESIGN_SPEC.read_text(encoding="utf-8")
    schema_sentence = re.search(r"The canonical transaction fields are ([^.]+)\.", design)

    assert schema_sentence is not None
    documented_columns = tuple(re.findall(r"`([^`]+)`", schema_sentence.group(1)))
    assert documented_columns == _transaction_columns_from_domain()
    assert "`is_fraud` is a synthetic boolean fraud label" in design


def test_sqlalchemy_guide_links_to_runnable_migrations_without_redefining_orm_setup() -> None:
    lesson = SQLALCHEMY_README.read_text(encoding="utf-8")

    assert "conceptual production examples" in lesson
    practice = REPOSITORY_ROOT / "modules/02_python_backend/exercises/schema_migrations/README.md"
    assert practice in (
        (SQLALCHEMY_README.parent / path).resolve()
        for path in _relative_markdown_targets(SQLALCHEMY_README)
    )


def test_progress_is_an_ordered_editable_module_01_to_08_checklist() -> None:
    """Learners can update the implemented lesson sequence as they progress."""
    entries = CHECKLIST_ENTRY.findall(PROGRESS_PATH.read_text(encoding="utf-8"))

    assert entries == [*PLANNED_LESSON_IDS, *READINESS_IDS, *APPLIED_TOOLS_IDS]


def test_progress_includes_every_loaded_catalog_lesson() -> None:
    """A catalog lesson cannot be released without a progress entry."""
    entries = set(CHECKLIST_ENTRY.findall(PROGRESS_PATH.read_text(encoding="utf-8")))
    lesson_ids = {
        item.identifier for item in Catalog.load(REPOSITORY_ROOT).items if item.kind == "lesson"
    }

    assert lesson_ids <= entries


def test_final_modules_expose_complete_registered_lesson_sequences() -> None:
    """RAG, agents and production must expose real lessons, not just starter directories."""
    catalog = Catalog.load(REPOSITORY_ROOT)
    for module in FINAL_MODULES:
        module_root = REPOSITORY_ROOT / "modules" / module
        readme = (REPOSITORY_ROOT / "modules" / module / "README.md").read_text(encoding="utf-8")
        assert "## Prerequisites" in readme
        lessons = [
            item
            for item in catalog.items
            if item.kind == "lesson" and item.readme.is_relative_to(module_root)
        ]
        assert len(lessons) == 6, module
        for lesson in lessons:
            content = lesson.readme.read_text(encoding="utf-8")
            for heading in (
                "Goal",
                "Java mental model",
                "Python model",
                "Key concepts",
                "Example",
                "Exercises",
                "Self-check",
                "Done when",
            ):
                assert f"## {heading}" in content, lesson.identifier
            assert (lesson.readme.parent / "example.py").is_file()
        exercises = [
            item
            for item in catalog.items
            if item.kind == "exercise" and item.readme.is_relative_to(module_root)
        ]
        expected_exercises = 9 if module in {"06_rag", "08_production_ai"} else 8
        assert len(exercises) == expected_exercises, module
        assert "The full lesson sequence is deferred." not in readme


def _relative_markdown_targets(document: Path) -> tuple[Path, ...]:
    """Return local Markdown destinations while excluding anchors and external links."""
    targets: list[Path] = []
    for raw_target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
        target = raw_target.split(maxsplit=1)[0].split("#", maxsplit=1)[0]
        if target and "://" not in target and not target.startswith(("#", "/", "mailto:")):
            targets.append(Path(target))
    return tuple(targets)


def _markdown_section(document: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        document,
    )
    assert match is not None, f"Missing section: {heading}"
    return match.group(1)


def _transaction_columns_from_domain() -> tuple[str, ...]:
    tree = ast.parse(TRANSACTION_DOMAIN.read_text(encoding="utf-8"))
    for statement in tree.body:
        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == "TRANSACTION_COLUMNS"
            and isinstance(statement.value, ast.Tuple)
        ):
            columns = tuple(
                element.value
                for element in statement.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )
            assert len(columns) == len(statement.value.elts)
            return columns
    raise AssertionError("TRANSACTION_COLUMNS must remain a literal tuple in domain.py")


def _fenced_command_lines(document: str) -> tuple[str, ...]:
    """Return non-empty, stripped lines from Markdown fenced code blocks."""
    return tuple(
        line.strip()
        for block in FENCED_CODE_BLOCK.findall(document)
        for line in block.splitlines()
        if line.strip()
    )
