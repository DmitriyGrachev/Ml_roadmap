"""Tracked-artifact and untouched-starter hygiene contracts."""

from __future__ import annotations

import ast
import subprocess
from itertools import pairwise
from pathlib import Path, PurePosixPath

from roadmap_tools.catalog import Catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_DIRECTORIES = frozenset(
    {
        ".idea",
        ".ipynb_checkpoints",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        ".vscode",
        "__pycache__",
        "htmlcov",
    }
)
FORBIDDEN_SUFFIXES = frozenset({".db", ".key", ".pem", ".pyc", ".pyo", ".sqlite", ".sqlite3"})
FORBIDDEN_ANSWER_NAMES = frozenset({"answer", "answers", "completed", "solution", "solutions"})
INTENTIONAL_INPUT_NAMES = frozenset({"broken.py", "review_me.py"})
BANKING_STARTER_FILES = (
    "projects/banking_ai_lab/banking_ai_lab/importer.py",
    "projects/banking_ai_lab/banking_ai_lab/analytics.py",
    "projects/banking_ai_lab/banking_ai_lab/dataframe.py",
    "projects/banking_ai_lab/banking_ai_lab/service.py",
    "projects/banking_ai_lab/banking_ai_lab/persistence.py",
)
EXPECTED_MULTI_BOUNDARIES = {
    "modules/02_python_backend/06_sqlalchemy/exercises/transaction_repository/starter.py": {
        "SqlAlchemyTransactionRepository.add",
        "SqlAlchemyTransactionRepository.get",
        "SqlAlchemyTransactionRepository.list_by_user",
    },
    "modules/03_data_foundations/06_fraud_metrics/exercises/confusion_metrics/starter.py": {
        "confusion_counts",
        "accuracy",
        "precision",
        "recall",
        "f1",
    },
    "modules/03_data_foundations/06_fraud_metrics/exercises/ranking_metrics/starter.py": {
        "roc_auc",
        "pr_auc",
    },
    "projects/banking_ai_lab/banking_ai_lab/analytics.py": {
        "build_report",
        "write_report_json",
    },
    "projects/banking_ai_lab/banking_ai_lab/dataframe.py": {
        "transaction_frame",
        "daily_currency_summary",
    },
    "projects/banking_ai_lab/banking_ai_lab/service.py": {
        "TransactionService.create_transaction",
        "TransactionService.get_transaction",
        "TransactionService.list_transactions",
    },
    "projects/banking_ai_lab/banking_ai_lab/persistence.py": {
        "SqlAlchemyTransactionRepository.create_transaction",
        "SqlAlchemyTransactionRepository.get_transaction",
        "SqlAlchemyTransactionRepository.list_transactions",
    },
}

EXPECTED_EXERCISE_BOUNDARIES = {
    "python-detect-duplicates": {"find_duplicate_ids"},
    "python-group-by-user": {"group_amounts_by_user"},
    "python-provider-frequency": {"provider_frequencies"},
    "python-sort-payments": {"sort_payments"},
    "python-filter-project-events": {"active_event_ids"},
    "python-slice-windows": {"transaction_windows"},
    "python-unpack-settlements": {"parse_settlement"},
    "python-configurable-filter": {"make_transaction_filter"},
    "python-combine-responses": {"combine_provider_responses"},
    "python-payment-processor-protocol": {"authorize_payment"},
    "python-transaction-report": {"build_transaction_report"},
    "python-payment-model": {"Payment.__post_init__"},
    "python-json-export": {"export_json_atomic"},
    "python-stream-transactions": {"stream_transactions"},
    "python-retry-gateway": {"retry.decorate.wrapped"},
    "python-mock-provider": {"request_quote"},
    "python-fetch-quotes": {"fetch_quotes"},
    "backend-transaction-contract": {"validate_transaction"},
    "backend-payment-router": {"build_payment_router"},
    "backend-error-mapping": {"register_payment_exception_handlers"},
    "backend-provider-fanout": {"fetch_provider_quotes"},
    "backend-transaction-repository": {
        "SqlAlchemyTransactionRepository.add",
        "SqlAlchemyTransactionRepository.get",
        "SqlAlchemyTransactionRepository.list_by_user",
    },
    "backend-postgres-query": {"daily_currency_totals"},
    "data-payment-matrix": {"convert_amount_matrix"},
    "data-transaction-summary": {"summarize_transactions"},
    "data-merchant-join": {"attach_merchant_risk"},
    "data-quality-report": {"assess_transaction_quality"},
    "data-statistical-profile": {"describe_amounts"},
    "data-bayes-alert": {"fraud_probability_given_alert"},
    "data-time-split": {"chronological_split"},
    "data-confusion-metrics": {
        "confusion_counts",
        "accuracy",
        "precision",
        "recall",
        "f1",
    },
    "data-ranking-metrics": {"roc_auc", "pr_auc"},
}

EXPECTED_BANKING_BOUNDARIES = {
    "projects/banking_ai_lab/banking_ai_lab/importer.py": {"import_transactions"},
    "projects/banking_ai_lab/banking_ai_lab/analytics.py": {
        "build_report",
        "write_report_json",
    },
    "projects/banking_ai_lab/banking_ai_lab/dataframe.py": {
        "transaction_frame",
        "daily_currency_summary",
    },
    "projects/banking_ai_lab/banking_ai_lab/service.py": {
        "TransactionService.create_transaction",
        "TransactionService.get_transaction",
        "TransactionService.list_transactions",
    },
    "projects/banking_ai_lab/banking_ai_lab/persistence.py": {
        "SqlAlchemyTransactionRepository.create_transaction",
        "SqlAlchemyTransactionRepository.get_transaction",
        "SqlAlchemyTransactionRepository.list_transactions",
    },
}


def tracked_files(repository_root: Path) -> tuple[str, ...]:
    """Return normalized Git-tracked paths without consulting ignored files."""

    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(path for path in result.stdout.split("\0") if path)


def hygiene_violation(path_text: str) -> str | None:
    """Classify repository artifacts that must never be tracked."""

    path = PurePosixPath(path_text.replace("\\", "/"))
    lower_parts = tuple(part.casefold() for part in path.parts)
    name = path.name.casefold()
    if any(part in FORBIDDEN_DIRECTORIES for part in lower_parts):
        return "local/cache directory"
    if name.startswith(".env") and name != ".env.example":
        return "environment file"
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return "local database/cache/secret file"
    if path.stem.casefold() in FORBIDDEN_ANSWER_NAMES or any(
        part in FORBIDDEN_ANSWER_NAMES for part in lower_parts[:-1]
    ):
        return "answer artifact"
    if (
        "generated-reports" in lower_parts
        or "derived-data" in lower_parts
        or any(parent == "data" and child == "derived" for parent, child in pairwise(lower_parts))
    ):
        return "generated or derived data"
    if "reports" in lower_parts or (path.suffix.casefold() == ".json" and "report" in path.stem):
        return "generated report"
    if name in {".coverage", "coverage.xml"}:
        return "coverage artifact"
    return None


def is_not_implemented_raise(statement: ast.stmt) -> bool:
    """Return whether a statement directly raises NotImplementedError."""

    if not isinstance(statement, ast.Raise) or statement.exc is None:
        return False
    exception = statement.exc.func if isinstance(statement.exc, ast.Call) else statement.exc
    return isinstance(exception, ast.Name) and exception.id == "NotImplementedError"


def static_truth_value(expression: ast.expr) -> bool | None:
    """Evaluate only literal truth values, never arbitrary Python expressions."""

    try:
        return bool(ast.literal_eval(expression))
    except (ValueError, TypeError):
        if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.Not):
            operand = static_truth_value(expression.operand)
            return None if operand is None else not operand
    return None


def block_may_complete(statements: list[ast.stmt]) -> bool:
    """Conservatively recognize a path that reaches the statement after a block."""

    for statement in statements:
        if isinstance(statement, (ast.Raise, ast.Return, ast.Break, ast.Continue)):
            return False
        if isinstance(statement, ast.If):
            truth = static_truth_value(statement.test)
            if truth is True:
                may_complete = block_may_complete(statement.body)
            elif truth is False:
                may_complete = block_may_complete(statement.orelse)
            else:
                may_complete = block_may_complete(statement.body) or block_may_complete(
                    statement.orelse
                )
            if not may_complete:
                return False
        elif isinstance(statement, ast.While):
            truth = static_truth_value(statement.test)
            if truth is True or not block_may_complete(statement.orelse):
                return False
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            if not block_may_complete(statement.body):
                return False
        elif isinstance(statement, ast.Try):
            if not block_may_complete(statement.finalbody):
                return False
            normal_path = block_may_complete(statement.body) and block_may_complete(
                statement.orelse
            )
            handler_path = any(block_may_complete(handler.body) for handler in statement.handlers)
            if not normal_path and not handler_path:
                return False
    return True


def own_scope_contains_return(statements: list[ast.stmt]) -> bool:
    """Find returns in this callable without descending into nested callables."""

    pending: list[ast.AST] = list(statements)
    while pending:
        node = pending.pop()
        if isinstance(node, ast.Return):
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        pending.extend(ast.iter_child_nodes(node))
    return False


def block_has_reachable_not_implemented(statements: list[ast.stmt]) -> bool:
    """Require the starter's canonical direct, final learner boundary."""

    return (
        bool(statements)
        and is_not_implemented_raise(statements[-1])
        and not own_scope_contains_return(statements[:-1])
        and block_may_complete(statements[:-1])
    )


def reachable_not_implemented_functions(path: Path) -> tuple[str, ...]:
    """List functions whose own control flow can reach the starter boundary."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    class BoundaryVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scope: list[str] = []
            self.boundaries: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_function(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_function(node)

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            self.scope.append(node.name)
            if block_has_reachable_not_implemented(node.body):
                self.boundaries.append(".".join(self.scope))
            self.generic_visit(node)
            self.scope.pop()

    visitor = BoundaryVisitor()
    visitor.visit(tree)
    return tuple(visitor.boundaries)


def test_tracked_tree_contains_no_local_generated_or_answer_artifacts() -> None:
    violations = {
        path: reason
        for path in tracked_files(REPOSITORY_ROOT)
        if (reason := hygiene_violation(path)) is not None
    }

    assert violations == {}


def test_hygiene_classifier_rejects_each_major_artifact_class() -> None:
    forbidden = (
        ".env",
        ".env.local",
        ".venv/pyvenv.cfg",
        ".idea/workspace.xml",
        "pkg/__pycache__/module.pyc",
        "notebooks/.ipynb_checkpoints/example.ipynb",
        "local.sqlite3",
        "generated/reports/summary.json",
        "generated-reports/summary.json",
        "data/derived/transactions.csv",
        "derived-data/model.parquet",
        "exercise/solution.py",
        "exercise/completed/starter.py",
    )

    assert all(hygiene_violation(path) is not None for path in forbidden)
    assert hygiene_violation("projects/banking_ai_lab/.env.example") is None
    assert hygiene_violation("modules/example/exercises/report/starter.py") is None
    assert hygiene_violation("generated_reports/README.md") is None
    assert hygiene_violation("data/derived-notes/README.md") is None
    assert hygiene_violation("derived-data-notes/README.md") is None


def test_every_cataloged_exercise_has_a_boundary_or_intentional_input() -> None:
    catalog = Catalog.load(REPOSITORY_ROOT)
    coding_exercises: set[str] = set()

    for item in catalog.items:
        if item.kind != "exercise":
            continue
        candidates = (
            item.readme.parent / "starter.py",
            item.readme.parent / "report.py",
            item.readme.parent / "broken.py",
            item.readme.parent / "review_me.py",
        )
        present = tuple(path for path in candidates if path.is_file())
        assert len(present) == 1, item.identifier
        source = present[0]
        if source.name in INTENTIONAL_INPUT_NAMES:
            continue
        coding_exercises.add(item.identifier)
        assert (
            set(reachable_not_implemented_functions(source))
            == (EXPECTED_EXERCISE_BOUNDARIES[item.identifier])
        ), item.identifier

    assert coding_exercises == set(EXPECTED_EXERCISE_BOUNDARIES)


def test_banking_project_keeps_all_student_owned_source_files_incomplete() -> None:
    catalog = Catalog.load(REPOSITORY_ROOT)
    assert catalog.get("banking-ai-lab").kind == "project"

    assert set(BANKING_STARTER_FILES) == set(EXPECTED_BANKING_BOUNDARIES)
    for relative_path in BANKING_STARTER_FILES:
        path = REPOSITORY_ROOT / relative_path
        assert (
            set(reachable_not_implemented_functions(path))
            == (EXPECTED_BANKING_BOUNDARIES[relative_path])
        ), relative_path


def test_every_multi_boundary_starter_keeps_each_student_function_incomplete() -> None:
    for relative_path, expected_functions in EXPECTED_MULTI_BOUNDARIES.items():
        actual_functions = set(reachable_not_implemented_functions(REPOSITORY_ROOT / relative_path))
        assert actual_functions == expected_functions, relative_path


def test_reachability_check_rejects_solved_and_dead_decoy_boundaries(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    starter.write_text("def solve() -> int:\n    return 1\n", encoding="utf-8")
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n    if False:\n        raise NotImplementedError\n    return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n    if 0:\n        raise NotImplementedError\n    return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n    while False:\n        raise NotImplementedError\n    return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n    for _ in ():\n        raise NotImplementedError\n    return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n"
        "    for _ in range(0):\n"
        "        raise NotImplementedError\n"
        "    return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> None:\n    while True:\n        pass\n    raise NotImplementedError\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n"
        "    try:\n"
        "        raise NotImplementedError\n"
        "    except NotImplementedError:\n"
        "        return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n"
        "    try:\n"
        "        return 1\n"
        "    except Exception:\n"
        "        raise NotImplementedError\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n"
        "    try:\n"
        "        raise NotImplementedError\n"
        "    finally:\n"
        "        return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n"
        "    try:\n"
        "        raise NotImplementedError\n"
        "    except Exception:\n"
        "        return 1\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def solve() -> int:\n"
        "    return 1\n\n"
        "def unused_helper() -> None:\n"
        "    raise NotImplementedError\n",
        encoding="utf-8",
    )
    assert set(reachable_not_implemented_functions(starter)) != {"solve"}

    starter.write_text(
        "def solve() -> int:\n    raise NotImplementedError('student boundary')\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ("solve",)
