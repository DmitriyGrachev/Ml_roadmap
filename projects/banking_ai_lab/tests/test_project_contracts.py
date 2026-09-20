"""Whole-project contracts for the seven-stage Banking AI Lab."""

from __future__ import annotations

import ast
import csv
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from banking_ai_lab.domain import TRANSACTION_COLUMNS, Transaction

from roadmap_tools.catalog import Catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = REPOSITORY_ROOT / "projects" / "banking_ai_lab"
STAGES_ROOT = PROJECT_ROOT / "stages"
POSTGRES_INTEGRATION_TEST = PROJECT_ROOT / "tests" / "test_postgres_integration.py"
POSTGRES_SETUP_GUIDE = "projects/banking_ai_lab/stages/05_postgresql/README.md"

EXPECTED_COLUMNS = (
    "id",
    "user_id",
    "amount",
    "currency",
    "merchant",
    "category",
    "timestamp",
    "status",
    "is_fraud",
)


@dataclass(frozen=True)
class StageContract:
    directory: str
    prerequisite: str
    minutes: tuple[int, int]
    editable_terms: tuple[str, ...]
    editable_paths: tuple[str, ...]
    command: str
    test_path: str


STAGE_CONTRACTS = (
    StageContract(
        "01_csv_validation",
        "../../../../docs/setup.md",
        (60, 90),
        ("import_transactions", "banking_ai_lab/importer.py"),
        ("banking_ai_lab/importer.py",),
        "uv run pytest projects/banking_ai_lab/tests/test_importer.py -q -rx",
        "projects/banking_ai_lab/tests/test_importer.py",
    ),
    StageContract(
        "02_json_reports",
        "../01_csv_validation/README.md",
        (75, 90),
        ("build_report", "write_report_json", "banking_ai_lab/analytics.py"),
        ("banking_ai_lab/analytics.py",),
        "uv run pytest projects/banking_ai_lab/tests/test_analytics.py -q -rx",
        "projects/banking_ai_lab/tests/test_analytics.py",
    ),
    StageContract(
        "03_pandas_analysis",
        "../02_json_reports/README.md",
        (60, 90),
        ("transaction_frame", "daily_currency_summary", "banking_ai_lab/dataframe.py"),
        ("banking_ai_lab/dataframe.py",),
        "uv run pytest projects/banking_ai_lab/tests/test_dataframe.py -q -rx",
        "projects/banking_ai_lab/tests/test_dataframe.py",
    ),
    StageContract(
        "04_fastapi",
        "../03_pandas_analysis/README.md",
        (60, 90),
        ("TransactionService", "create_transaction", "get_transaction", "list_transactions"),
        ("banking_ai_lab/service.py",),
        "uv run pytest projects/banking_ai_lab/tests/test_api.py -q -rx",
        "projects/banking_ai_lab/tests/test_api.py",
    ),
    StageContract(
        "05_postgresql",
        "../04_fastapi/README.md",
        (75, 90),
        ("SqlAlchemyTransactionRepository", "banking_ai_lab/persistence.py"),
        ("banking_ai_lab/persistence.py",),
        "uv run pytest projects/banking_ai_lab/tests/test_persistence.py -q -rx",
        "projects/banking_ai_lab/tests/test_persistence.py",
    ),
    StageContract(
        "06_testing",
        "../05_postgresql/README.md",
        (30, 45),
        ("test_api.py", "test_persistence.py", "test_postgres_integration.py"),
        (
            "tests/test_api.py",
            "tests/test_persistence.py",
            "tests/test_postgres_integration.py",
        ),
        "uv run pytest projects/banking_ai_lab -q -rx",
        "projects/banking_ai_lab/tests",
    ),
    StageContract(
        "07_exploratory_analysis",
        "../06_testing/README.md",
        (45, 90),
        ("transaction_eda.ipynb", "exercise"),
        ("notebooks/transaction_eda.ipynb",),
        "uv run pytest projects/banking_ai_lab/tests/test_notebook.py -q",
        "projects/banking_ai_lab/tests/test_notebook.py",
    ),
)


def test_project_contains_exactly_seven_numbered_stage_guides_in_order() -> None:
    stage_directories = tuple(
        path.name
        for path in sorted(STAGES_ROOT.iterdir())
        if path.is_dir() and re.fullmatch(r"\d{2}_[a-z0-9_]+", path.name)
    )

    assert stage_directories == tuple(contract.directory for contract in STAGE_CONTRACTS)
    assert all((STAGES_ROOT / name / "README.md").is_file() for name in stage_directories)


def test_every_stage_guide_is_actionable_linked_and_placeholder_free() -> None:
    for contract in STAGE_CONTRACTS:
        readme = STAGES_ROOT / contract.directory / "README.md"
        text = readme.read_text(encoding="utf-8")

        assert re.search(r"^## Prerequisites\s*$", text, re.MULTILINE)
        assert re.search(r"^## (?:Estimated time|Time box)\s*$", text, re.MULTILINE)
        assert re.search(r"^## (?:Edit|Editable surface)\s*$", text, re.MULTILINE)
        assert re.search(r"^## (?:Run|Run the contracts)\s*$", text, re.MULTILINE)
        assert re.search(r"^## Acceptance criteria\s*$", text, re.MULTILINE)
        assert re.search(r"^## Hints(?: \(optional\))?\s*$", text, re.MULTILINE)
        assert re.search(r"^## Completion checklist\s*$", text, re.MULTILINE)

        assert f"]({contract.prerequisite})" in text
        prerequisite = (readme.parent / contract.prerequisite).resolve()
        assert prerequisite.is_relative_to(REPOSITORY_ROOT)
        assert prerequisite.is_file()

        lower, upper = contract.minutes
        assert re.search(
            rf"{lower}\s*(?:-|\N{{EN DASH}})\s*{upper}\s+minutes",
            text,
            re.IGNORECASE,
        )
        for term in contract.editable_terms:
            assert term in text
        for editable_path in contract.editable_paths:
            assert (PROJECT_ROOT / editable_path).is_file()

        assert contract.command in text
        assert (REPOSITORY_ROOT / contract.test_path).exists()
        assert (
            re.search(
                r"\b(?:TODO|TBD|coming soon|placeholder)\b",
                text,
                re.IGNORECASE,
            )
            is None
        )

        sections = re.split(r"(?m)^## ", text)[1:]
        assert sections
        assert all(
            "\n\n" in section and section.split("\n\n", 1)[1].strip() for section in sections
        )
        checklist = text.split("## Completion checklist", 1)[1]
        assert len(re.findall(r"(?m)^- \[ \] ", checklist)) >= 3


def test_all_local_markdown_links_resolve_inside_the_repository() -> None:
    readmes = [PROJECT_ROOT / "README.md"] + [
        STAGES_ROOT / contract.directory / "README.md" for contract in STAGE_CONTRACTS
    ]

    for readme in readmes:
        text = readme.read_text(encoding="utf-8")
        local_targets = [
            target.split("#", 1)[0]
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
            if not re.match(r"^[a-z][a-z0-9+.-]*://", target, re.IGNORECASE)
            and not target.startswith("#")
        ]
        assert local_targets
        for target in local_targets:
            resolved = (readme.parent / target).resolve()
            assert resolved.is_relative_to(REPOSITORY_ROOT)
            assert resolved.exists()


def test_project_readme_has_the_complete_linked_seven_stage_progression() -> None:
    readme = PROJECT_ROOT / "README.md"
    rows = tuple(
        line.strip()
        for line in readme.read_text(encoding="utf-8").splitlines()
        if re.match(r"^\| \[\d{2}\]\(", line)
    )
    expected_rows = (
        "| [01](stages/01_csv_validation/README.md) | Validate transaction CSV rows | Ready |",
        (
            "| [02](stages/02_json_reports/README.md) | Build analytics and atomic JSON reports "
            "| Ready |"
        ),
        "| [03](stages/03_pandas_analysis/README.md) | Analyze transactions with Pandas | Ready |",
        (
            "| [04](stages/04_fastapi/README.md) | Expose selected operations through FastAPI "
            "| Ready |"
        ),
        (
            "| [05](stages/05_postgresql/README.md) | Persist transactions with PostgreSQL and "
            "SQLAlchemy | Ready |"
        ),
        "| [06](stages/06_testing/README.md) | Add API and database integration tests | Ready |",
        (
            "| [07](stages/07_exploratory_analysis/README.md) | Explore transaction and fraud "
            "patterns in a notebook | Ready |"
        ),
    )

    assert rows == expected_rows
    for target in re.findall(r"\]\((stages/[^)]+/README\.md)\)", "\n".join(rows)):
        assert (readme.parent / target).is_file()


def test_transaction_schema_is_the_exact_nine_field_project_contract() -> None:
    with (REPOSITORY_ROOT / "datasets" / "transactions.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        fieldnames = csv.DictReader(source).fieldnames

    assert TRANSACTION_COLUMNS == EXPECTED_COLUMNS
    assert tuple(Transaction.model_fields) == EXPECTED_COLUMNS
    assert tuple(fieldnames or ()) == EXPECTED_COLUMNS


def test_catalog_exposes_the_exact_banking_project_paths() -> None:
    with (REPOSITORY_ROOT / "curriculum.toml").open("rb") as source:
        document: dict[str, Any] = tomllib.load(source)
    records = document.get("items")

    assert isinstance(records, list)
    matching = [record for record in records if record.get("id") == "banking-ai-lab"]
    assert matching == [
        {
            "id": "banking-ai-lab",
            "title": "Banking AI Lab",
            "kind": "project",
            "readme": "projects/banking_ai_lab/README.md",
            "tests": ["projects/banking_ai_lab"],
        }
    ]

    item = Catalog.load(REPOSITORY_ROOT).get("banking-ai-lab")
    assert item.readme == (PROJECT_ROOT / "README.md").resolve()
    assert item.tests == (PROJECT_ROOT.resolve(),)


def test_environment_and_compose_keep_the_complete_local_contract() -> None:
    env_text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    compose = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    env_keys = tuple(
        line.split("=", 1)[0]
        for line in env_text.splitlines()
        if line and not line.startswith("#") and "=" in line
    )

    assert env_keys == (
        "BANKING_DATABASE_URL",
        "BANKING_LOG_LEVEL",
        "BANKING_API_PREFIX",
        "BANKING_POSTGRES_USER",
        "BANKING_POSTGRES_PASSWORD",
        "BANKING_POSTGRES_DB",
        "BANKING_POSTGRES_PORT",
        "BANKING_APP_PORT",
        "ROADMAP_POSTGRES_URL",
    )
    document = yaml.safe_load(compose)
    assert isinstance(document, dict)
    services = document["services"]
    assert set(services) == {"app", "postgres"}
    assert "pg_isready" in " ".join(services["postgres"]["healthcheck"]["test"])
    assert services["app"]["depends_on"]["postgres"]["condition"] == "service_healthy"
    assert services["postgres"]["volumes"] == ["postgres_data:/var/lib/postgresql/data"]
    assert all(
        port.startswith("127.0.0.1:") for service in services.values() for port in service["ports"]
    )


def test_postgres_skip_reason_points_to_the_complete_setup_guide() -> None:
    """An unconfigured run must identify both the opt-in variable and the full setup workflow."""
    tree = ast.parse(POSTGRES_INTEGRATION_TEST.read_text(encoding="utf-8"))
    assignment = next(
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "POSTGRES_SKIP_REASON"
            for target in statement.targets
        )
    )
    reason = ast.literal_eval(assignment.value)

    assert reason == (
        "Set ROADMAP_POSTGRES_URL after following "
        "projects/banking_ai_lab/stages/05_postgresql/README.md"
    )
    assert (REPOSITORY_ROOT / POSTGRES_SETUP_GUIDE).is_file()


def test_stage_seven_documents_both_notebook_workflows_and_reset_contract() -> None:
    text = (STAGES_ROOT / "07_exploratory_analysis" / "README.md").read_text(encoding="utf-8")

    for term in (
        "PyCharm",
        "Jupyter",
        "Colab",
        "45\u201390 minutes",
        "datasets/transactions.csv",
        "RANDOM_SEED = 20260919",
        "Restart Kernel and Clear All Outputs",
        "NotImplementedError",
        "missing-value",
        "duplicate",
        "distribution",
        "aggregation",
        "temporal",
        "fraud-metric",
    ):
        assert term in text
    assert "uv run jupyter lab projects/banking_ai_lab/notebooks/transaction_eda.ipynb" in text
    assert "uv run pytest projects/banking_ai_lab/tests/test_notebook.py -q" in text
