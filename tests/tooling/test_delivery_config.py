from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_runtime_dependencies_include_an_asgi_server() -> None:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as project_file:
        project = tomllib.load(project_file)

    dependencies = project["project"]["dependencies"]

    assert any(dependency.startswith("uvicorn") for dependency in dependencies)


def test_httpx2_is_available_only_as_a_development_dependency() -> None:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as project_file:
        project = tomllib.load(project_file)

    runtime_dependencies = project["project"]["dependencies"]
    development_dependencies = project["dependency-groups"]["dev"]

    assert not any(dependency.startswith("httpx2") for dependency in runtime_dependencies)
    assert any(dependency.startswith("httpx2") for dependency in development_dependencies)


def test_docker_build_context_excludes_local_and_secret_files() -> None:
    patterns = {
        line.strip()
        for line in (REPOSITORY_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert {".git", ".venv", ".env", ".idea", "**/__pycache__", "*.db"} <= patterns


def test_compose_example_binds_postgres_only_to_loopback() -> None:
    compose = (
        REPOSITORY_ROOT
        / "modules"
        / "02_python_backend"
        / "09_docker_delivery"
        / "compose.example.yaml"
    ).read_text(encoding="utf-8")

    assert '      - "127.0.0.1:5432:5432"' in compose.splitlines()
