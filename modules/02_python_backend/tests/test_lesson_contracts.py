import hashlib
import importlib.util
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODULE_ROOT = Path(__file__).resolve().parents[1]

LESSON_DIRECTORIES = (
    "01_fastapi",
    "02_pydantic",
    "03_architecture_dependencies",
    "04_config_errors_logging",
    "05_async_endpoints",
    "06_sqlalchemy",
    "07_postgresql",
    "08_api_integration_testing",
    "09_docker_delivery",
)
SHARED_HEADINGS = (
    "Goal",
    "Java mental model",
    "Python model",
    "Key concepts",
    "Example",
    "Exercises",
    "Self-check",
    "Done when",
)
EXERCISE_READMES = {
    "02_pydantic": "exercises/transaction_contract/README.md",
    "03_architecture_dependencies": "exercises/payment_router/README.md",
    "04_config_errors_logging": "exercises/error_mapping/README.md",
    "05_async_endpoints": "exercises/provider_fanout/README.md",
    "06_sqlalchemy": "exercises/transaction_repository/README.md",
    "07_postgresql": "exercises/postgres_query/README.md",
    "08_api_integration_testing": "exercises/api_test_review/README.md",
}
STARTER_PATHS = (
    "02_pydantic/exercises/transaction_contract/starter.py",
    "03_architecture_dependencies/exercises/payment_router/starter.py",
    "04_config_errors_logging/exercises/error_mapping/starter.py",
    "05_async_endpoints/exercises/provider_fanout/starter.py",
    "06_sqlalchemy/exercises/transaction_repository/starter.py",
    "07_postgresql/exercises/postgres_query/starter.py",
    "exercises/conditional_cache/starter.py",
    "exercises/equipment_repository/starter.py",
    "exercises/library_search/starter.py",
    "exercises/room_booking_api/starter.py",
)


def _lesson_readmes() -> list[Path]:
    return sorted(MODULE_ROOT.glob("[0-9][0-9]_*/README.md"))


def _section(markdown: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        markdown,
    )
    assert match is not None, f"Missing section: {heading}"
    return match.group(1)


def test_exactly_nine_numbered_lessons_keep_shared_headings_in_order() -> None:
    readmes = _lesson_readmes()

    assert [readme.parent.name for readme in readmes] == list(LESSON_DIRECTORIES)
    assert MODULE_ROOT / "README.md" not in readmes
    for readme in readmes:
        markdown = readme.read_text(encoding="utf-8")
        headings = re.findall(r"(?m)^## (.+?)\s*$", markdown)
        positions = [headings.index(heading) for heading in SHARED_HEADINGS]

        assert positions == sorted(positions), readme


def test_every_lesson_has_a_real_spring_comparison_and_five_self_checks() -> None:
    for readme in _lesson_readmes():
        markdown = readme.read_text(encoding="utf-8")
        java_model = _section(markdown, "Java mental model")
        comparison_rows = [
            line
            for line in java_model.splitlines()
            if line.startswith("|") and "---" not in line and "Spring | Python" not in line
        ]
        questions = re.findall(r"(?m)^\d+\. .+\?\s*$", _section(markdown, "Self-check"))

        assert "| Spring | Python" in java_model, readme
        assert len(comparison_rows) >= 2, readme
        assert "**Non-equivalence:**" in java_model, readme
        assert len(questions) >= 5, readme


def test_each_owned_exercise_has_a_valid_repository_path_link() -> None:
    for lesson_directory, expected_target in EXERCISE_READMES.items():
        readme = MODULE_ROOT / lesson_directory / "README.md"
        markdown = readme.read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", _section(markdown, "Exercises"))
        resolved_links = {(readme.parent / link).resolve() for link in links}
        expected_path = (readme.parent / expected_target).resolve()

        assert expected_path in resolved_links, readme
        assert expected_path.is_relative_to(REPOSITORY_ROOT), expected_path
        assert expected_path.is_file(), expected_path


def test_database_and_delivery_warnings_pin_optional_boundaries() -> None:
    sqlalchemy_lesson = (MODULE_ROOT / "06_sqlalchemy/README.md").read_text(encoding="utf-8")
    postgres_lesson = (MODULE_ROOT / "07_postgresql/README.md").read_text(encoding="utf-8")
    docker_lesson = (MODULE_ROOT / "09_docker_delivery/README.md").read_text(encoding="utf-8")

    assert (
        "> **Local-only database:** SQLite keeps the core exercise local; it does not replace "
        "the opt-in PostgreSQL dialect check in Lesson 07."
    ) in sqlalchemy_lesson
    assert (
        "> **PostgreSQL is optional:** ordinary module tests do not require Docker or a running "
        "PostgreSQL server."
    ) in postgres_lesson
    assert "Set ROADMAP_POSTGRES_URL and run: docker compose up -d postgres" in postgres_lesson
    assert (
        "Copy-Item modules/02_python_backend/09_docker_delivery/compose.example.yaml compose.yaml"
        in postgres_lesson
    )
    assert "docker compose up -d postgres" in postgres_lesson
    assert (
        "> **Docker is optional:** the module's examples and exercises run without building an "
        "image or starting Compose."
    ) in docker_lesson


def test_every_backend_starter_imports_under_a_collision_safe_name() -> None:
    starters = sorted(MODULE_ROOT.rglob("starter.py"))

    assert [path.relative_to(MODULE_ROOT).as_posix() for path in starters] == list(STARTER_PATHS)
    for starter in starters:
        relative_path = starter.relative_to(MODULE_ROOT).as_posix()
        digest = hashlib.sha256(relative_path.encode()).hexdigest()
        module_name = f"_roadmap_backend_starter_{digest}"
        spec = importlib.util.spec_from_file_location(module_name, starter)

        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(module_name, None)
