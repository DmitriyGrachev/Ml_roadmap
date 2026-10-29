"""Tracked-artifact and untouched-starter hygiene contracts."""

from __future__ import annotations

import ast
import subprocess
from itertools import pairwise
from pathlib import Path, PurePosixPath

import pytest

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
    "modules/01_python_core/exercises/interview_patterns/starter.py": {
        "lower_bound",
        "top_k",
        "reachable",
    },
    "modules/04_machine_learning/exercises/forecasting_intro/starter.py": {
        "features_at",
        "run_study",
    },
    "labs/01_pytorch_foundations/exercises/resume_training/starter.py": {
        "capture_state",
        "restore_state",
    },
    "modules/02_python_backend/exercises/equipment_repository/starter.py": {
        "EquipmentRepository.add",
        "EquipmentRepository.list_all",
    },
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
    "data-vectorized-features": {"masked_standardize", "topk_cosine"},
    "data-point-in-time-features": {"build_point_in_time_features"},
    "ml-sklearn-selection": {"select_pipeline", "permutation_report"},
    "lab-hf-trainer-workflow": {
        "tokenize_dataset",
        "build_collator",
        "make_training_arguments",
        "compute_metrics",
        "train_model",
    },
    "lab-token-classification": {"align_labels", "entity_metrics", "train_token_classifier"},
    "lab-sft-lora": {
        "validate_conversations",
        "split_conversations",
        "encode_conversation",
        "build_trainer",
        "compare_and_reload",
    },
    "lab-training-efficiency": {"accumulated_step"},
    "rag-neural-reranking": {"rerank", "ranking_metrics"},
    "rag-embedding-adaptation": {"make_triples", "split_queries", "fit_encoder"},
    "ml-experiment-management": {"select_trial", "build_objective", "run_search"},
    "lab-vllm-measurements": {"summarize_measurements"},
    "production-service-lifecycle": {"summarize_outcomes", "run_lifecycle", "join_delayed_labels"},
    "ml-data-pipeline": {"initialize", "snapshot", "load_increment"},
    "rag-end-to-end-evaluation": {"pool_tokens", "answer_case"},
    "ml-gradient-derivations": {"weighted_objective_gradient"},
    "ml-linear-geometry": {"principal_components", "centered_ridge"},
    "ml-tree-boosting": {"boost_predict", "best_gini_split"},
    "data-training-stability": {"paired_accuracy_interval", "classification_sweep"},
    "python-async-lifecycle": {"first_healthy"},
    "python-package-delivery": {"deliver"},
    "backend-schema-migrations": {"downgrade_database", "upgrade_database"},
    "python-control-flow": {"count_long_labels"},
    "data-experiment-design": {"bonferroni_rejections"},
    "ml-representation-study": {"reconstruct_from_components"},
    "ml-bias-slices": {"grouped_slices"},
    "backend-sql-foundations": {"latest_valid_measurements_sql"},
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
    "backend-analytics-sql": {"analytics_query"},
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
    "python-calendar-intervals": {"merge_intervals"},
    "backend-library-search": {"create_app"},
    "data-weather-quality": {"summarize_weather"},
    "rag-text-chunking": {"chunk_document"},
    "agents-workflow-schedule": {"schedule_workflow"},
    "production-request-metrics": {"summarize_requests"},
    "rag-vector-search": {"vector_search"},
    "rag-rank-fusion": {"fuse_rankings"},
    "rag-citation-validation": {"validate_citations"},
    "rag-retrieval-evaluation": {"evaluate_retrieval"},
    "agents-tool-dispatch": {"dispatch_tool"},
    "agents-bounded-loop": {"run_agent"},
    "agents-checkpoint-resume": {"resume_checkpoint"},
    "agents-trace-evaluation": {"evaluate_traces"},
    "production-release-gate": {"evaluate_release"},
    "production-budget-reservation": {"summarize_budget"},
    "production-redact-events": {"redact_events"},
    "production-rollout-decision": {"decide_rollout"},
    "ml-group-safe-split": {"split_sensor_groups"},
    "ml-mixed-feature-pipeline": {"build_visit_pipeline"},
    "ml-model-comparison": {"compare_regressors"},
    "ml-evaluation-report": {"build_evaluation_report"},
    "llm-prompt-messages": {"build_messages"},
    "llm-event-contract": {"parse_event"},
    "llm-context-budget": {"pack_context"},
    "llm-answer-evaluation": {"evaluate_answers"},
    "llm-bounded-retry": {"invoke_with_retry"},
    "python-word-index": {"build_word_index"},
    "python-paged-stream": {"iter_pages"},
    "python-interview-patterns": {"lower_bound", "top_k", "reachable"},
    "python-bounded-fetch": {"fetch_bounded"},
    "backend-room-booking-api": {"create_app"},
    "backend-conditional-cache": {"create_app"},
    "backend-equipment-repository": {"EquipmentRepository.add", "EquipmentRepository.list_all"},
    "data-image-pooling": {"block_means"},
    "data-library-joins": {"build_loan_report"},
    "data-paired-observations": {"summarize_pairs"},
    "data-paired-model-comparison": {"paired_difference"},
    "data-randomized-experiment": {"aggregate_units"},
    "ml-knn-mechanics": {"KNNClassifier.fit", "KNNClassifier.predict"},
    "ml-tabular-study": {"run_experiment"},
    "ml-evaluation-case": {"investigate"},
    "production-product-study": {"run_study"},
    "rag-ranking-study": {"run_study"},
    "ml-forecasting-intro": {"features_at", "run_study"},
    "lab-training-resume": {"capture_state", "restore_state"},
    "lab-attention-mechanics": {"attention"},
    "data-release-study": {"build_release"},
    "lab-training-diagnostics": {"investigate"},
    "ml-time-series-split": {"chronological_split"},
    "ml-multiclass-report": {"multiclass_report"},
    "ml-threshold-policy": {"choose_threshold"},
    "llm-context-packing": {"pack_context"},
    "llm-response-cache": {"cache_response"},
    "llm-stream-assembly": {"assemble_stream"},
    "rag-index-sync": {"plan_index_sync"},
    "rag-context-diversity": {"select_evidence"},
    "rag-retrieval-regression": {"compare_retrieval"},
    "agents-plan-validation": {"validate_plan"},
    "agents-handoff-packet": {"build_handoff"},
    "agents-tool-result-routing": {"route_result"},
    "production-artifact-manifest": {"validate_manifest"},
    "production-error-budget": {"summarize_error_budget"},
    "production-retention-policy": {"plan_retention"},
    "document-a1-reproduction": {"run_reproduction"},
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


EXPECTED_NESTED_AND_PROJECT_BOUNDARIES = {
    "labs/04_llm_finetuning/sft_workflow/learner_run.py": {"run_project"},
    (
        "modules/01_python_core/exercises/package_delivery/student_project/"
        "src/ticket_features/transform.py"
    ): {"transform"},
    (
        "modules/01_python_core/exercises/package_delivery/student_project/"
        "src/ticket_features/train.py"
    ): {"training_matrix"},
    (
        "modules/01_python_core/exercises/package_delivery/student_project/"
        "src/ticket_features/serve.py"
    ): {"serving_vector"},
    (
        "modules/02_python_backend/exercises/schema_migrations/"
        "student_migrations/versions/0002_body_length.py"
    ): {"upgrade", "downgrade"},
    "projects/external_tabular/starter.py": {"run_experiment"},
    "projects/document_intelligence_lab/external_model_study/starter.py": {"run_study"},
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


def node_obviously_binds_wraps(node: ast.AST) -> bool:
    """Recognize ordinary bindings that can replace the imported ``wraps`` name."""

    return (
        (
            isinstance(node, ast.Name)
            and node.id == "wraps"
            and isinstance(node.ctx, (ast.Store, ast.Del))
        )
        or (isinstance(node, ast.arg) and node.arg == "wraps")
        or (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == "wraps"
        )
        or (isinstance(node, ast.ExceptHandler) and node.name == "wraps")
        or (isinstance(node, (ast.Global, ast.Nonlocal)) and "wraps" in node.names)
    )


def module_has_unshadowed_wraps_import(tree: ast.Module) -> bool:
    """Recognize the retry starter's exact, unshadowed ``functools.wraps`` import."""

    top_level_nodes = set(tree.body)
    exact_imports = 0
    shadowed = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound_name = alias.asname or alias.name
                if bound_name != "wraps":
                    continue
                if (
                    node in top_level_nodes
                    and node.module == "functools"
                    and node.level == 0
                    and alias.name == "wraps"
                    and alias.asname is None
                ):
                    exact_imports += 1
                else:
                    shadowed = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                bound_name = alias.asname or alias.name.split(".", maxsplit=1)[0]
                if bound_name == "wraps":
                    shadowed = True
        elif node_obviously_binds_wraps(node):
            shadowed = True

    return exact_imports == 1 and not shadowed


def boundary_decorators_are_allowed(
    qualified_name: str,
    decorators: list[ast.expr],
    *,
    has_unshadowed_wraps_import: bool,
) -> bool:
    """Allow no boundary decorator except retry's exact metadata-preserving wrapper."""

    if not decorators:
        return True
    if (
        qualified_name != "retry.decorate.wrapped"
        or not has_unshadowed_wraps_import
        or len(decorators) != 1
    ):
        return False

    decorator = decorators[0]
    return (
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "wraps"
        and len(decorator.args) == 1
        and isinstance(decorator.args[0], ast.Name)
        and decorator.args[0].id == "operation"
        and not decorator.keywords
    )


def is_literal_globals_target(node: ast.Subscript, name: str) -> bool:
    """Return whether *node* statically targets ``globals()[name]``."""

    namespace = node.value
    return (
        isinstance(namespace, ast.Call)
        and isinstance(namespace.func, ast.Name)
        and namespace.func.id == "globals"
        and not namespace.args
        and not namespace.keywords
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == name
    )


def scope_rebinds_name_after(
    owner: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    definition: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Find transparent rebinding after *definition* in its owning lexical scope."""

    definition_end = (
        definition.end_lineno if definition.end_lineno is not None else definition.lineno
    )
    found = False

    class RebindingVisitor(ast.NodeVisitor):
        def binds_boundary_after(self, node: ast.AST, name: str | None) -> None:
            nonlocal found
            if name == definition.name and getattr(node, "lineno", 0) > definition_end:
                found = True

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.binds_boundary_after(node, node.name)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.binds_boundary_after(node, node.name)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.binds_boundary_after(node, node.name)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return None

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                self.binds_boundary_after(node, node.id)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                self.binds_boundary_after(
                    node,
                    alias.asname or alias.name.split(".", maxsplit=1)[0],
                )

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            nonlocal found
            for alias in node.names:
                if alias.name == "*":
                    if node.lineno > definition_end:
                        found = True
                    continue
                self.binds_boundary_after(node, alias.asname or alias.name)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            self.binds_boundary_after(node, node.name)
            self.generic_visit(node)

        def visit_MatchAs(self, node: ast.MatchAs) -> None:
            self.binds_boundary_after(node, node.name)
            self.generic_visit(node)

        def visit_MatchStar(self, node: ast.MatchStar) -> None:
            self.binds_boundary_after(node, node.name)

        def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
            self.binds_boundary_after(node, node.rest)
            self.generic_visit(node)

        def visit_ListComp(self, node: ast.ListComp) -> None:
            self.visit_comprehension_expressions(node, (node.elt,))

        def visit_SetComp(self, node: ast.SetComp) -> None:
            self.visit_comprehension_expressions(node, (node.elt,))

        def visit_DictComp(self, node: ast.DictComp) -> None:
            self.visit_comprehension_expressions(node, (node.key, node.value))

        def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
            self.visit_comprehension_expressions(node, (node.elt,))

        def visit_comprehension_expressions(
            self,
            node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
            values: tuple[ast.expr, ...],
        ) -> None:
            for generator in node.generators:
                self.visit(generator.iter)
                for condition in generator.ifs:
                    self.visit(condition)
            for value in values:
                self.visit(value)

        def visit_Subscript(self, node: ast.Subscript) -> None:
            nonlocal found
            if (
                isinstance(owner, ast.Module)
                and node.lineno > definition_end
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and is_literal_globals_target(node, definition.name)
            ):
                found = True
            self.generic_visit(node)

    visitor = RebindingVisitor()
    for statement in owner.body:
        visitor.visit(statement)
    return found


def module_rebinds_class_boundary_after(
    tree: ast.Module,
    class_owner: ast.ClassDef,
    boundary: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Recognize direct module-level replacement of a class learner boundary."""

    class_end = class_owner.end_lineno if class_owner.end_lineno is not None else class_owner.lineno
    found = False

    class ClassBoundaryRebindingVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return None

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return None

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return None

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return None

        def visit_Attribute(self, node: ast.Attribute) -> None:
            nonlocal found
            if (
                node.lineno > class_end
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and node.attr == boundary.name
                and isinstance(node.value, ast.Name)
                and node.value.id == class_owner.name
            ):
                found = True
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            nonlocal found
            if (
                node.lineno > class_end
                and isinstance(node.func, ast.Name)
                and node.func.id in {"delattr", "setattr"}
                and (
                    (node.func.id == "setattr" and len(node.args) == 3)
                    or (node.func.id == "delattr" and len(node.args) == 2)
                )
                and not node.keywords
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == class_owner.name
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == boundary.name
            ):
                found = True
            self.generic_visit(node)

    visitor = ClassBoundaryRebindingVisitor()
    for statement in tree.body:
        visitor.visit(statement)
    return found


def reachable_not_implemented_functions(path: Path) -> tuple[str, ...]:
    """List functions whose own control flow can reach the starter boundary."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    has_unshadowed_wraps_import = module_has_unshadowed_wraps_import(tree)

    class BoundaryVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scope: list[str] = []
            self.owners: list[
                ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
            ] = [tree]
            self.boundaries: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.scope.append(node.name)
            self.owners.append(node)
            self.generic_visit(node)
            self.owners.pop()
            self.scope.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_function(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_function(node)

        def _boundary_is_rebound(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
            definitions = [
                definition
                for definition in (*self.owners[1:], node)
                if not isinstance(definition, ast.Module)
            ]
            if any(
                scope_rebinds_name_after(owner, definition)
                for owner, definition in zip(self.owners, definitions, strict=True)
            ):
                return True

            return (
                len(self.owners) == 2
                and isinstance(self.owners[0], ast.Module)
                and isinstance(self.owners[1], ast.ClassDef)
                and module_rebinds_class_boundary_after(self.owners[0], self.owners[1], node)
            )

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            self.scope.append(node.name)
            qualified_name = ".".join(self.scope)
            if (
                block_has_reachable_not_implemented(node.body)
                and boundary_decorators_are_allowed(
                    qualified_name,
                    node.decorator_list,
                    has_unshadowed_wraps_import=has_unshadowed_wraps_import,
                )
                and not self._boundary_is_rebound(node)
            ):
                self.boundaries.append(qualified_name)
            self.owners.append(node)
            self.generic_visit(node)
            self.owners.pop()
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


@pytest.mark.maintainer_only
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


@pytest.mark.maintainer_only
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


@pytest.mark.maintainer_only
def test_every_multi_boundary_starter_keeps_each_student_function_incomplete() -> None:
    for relative_path, expected_functions in EXPECTED_MULTI_BOUNDARIES.items():
        actual_functions = set(reachable_not_implemented_functions(REPOSITORY_ROOT / relative_path))
        assert actual_functions == expected_functions, relative_path


@pytest.mark.maintainer_only
def test_nested_delivery_and_external_project_starters_remain_incomplete() -> None:
    for relative_path, expected in EXPECTED_NESTED_AND_PROJECT_BOUNDARIES.items():
        actual = set(reachable_not_implemented_functions(REPOSITORY_ROOT / relative_path))
        assert actual == expected, relative_path


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


def test_reachability_check_rejects_a_solving_decorator(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    starter.write_text(
        "def replace_with_solution(operation):\n"
        "    del operation\n"
        "    def completed() -> int:\n"
        "        return 1\n"
        "    return completed\n\n"
        "@replace_with_solution\n"
        "def solve() -> int:\n"
        "    raise NotImplementedError('hidden behind a solution')\n",
        encoding="utf-8",
    )

    assert reachable_not_implemented_functions(starter) == ()


def test_reachability_check_allows_the_exact_retry_wraps_decorator() -> None:
    retry_starter = (
        REPOSITORY_ROOT / "modules/01_python_core/08_decorators/exercises/retry_gateway/starter.py"
    )

    assert reachable_not_implemented_functions(retry_starter) == ("retry.decorate.wrapped",)


def test_retry_wraps_exception_rejects_aliasing_and_shadowing(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    starter.write_text(
        "from functools import wraps as preserve\n\n"
        "def retry():\n"
        "    def decorate(operation):\n"
        "        @preserve(operation)\n"
        "        def wrapped():\n"
        "            raise NotImplementedError('aliased wraps')\n"
        "        return wrapped\n"
        "    return decorate\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "from functools import wraps\n\n"
        "def replace_with_solution(operation):\n"
        "    return operation\n\n"
        "wraps = replace_with_solution\n\n"
        "def retry():\n"
        "    def decorate(operation):\n"
        "        @wraps(operation)\n"
        "        def wrapped():\n"
        "            raise NotImplementedError('shadowed wraps')\n"
        "        return wrapped\n"
        "    return decorate\n",
        encoding="utf-8",
    )
    assert reachable_not_implemented_functions(starter) == ()


def test_reachability_check_rejects_literal_globals_rebinding_after_boundary(
    tmp_path: Path,
) -> None:
    starter = tmp_path / "starter.py"
    starter.write_text(
        "def solve() -> int:\n"
        "    raise NotImplementedError('student boundary')\n\n"
        "def _completed_solve() -> int:\n"
        "    return 1\n\n"
        'globals()["solve"] = _completed_solve\n',
        encoding="utf-8",
    )

    assert reachable_not_implemented_functions(starter) == ()


def test_reachability_check_rejects_post_definition_scope_rebinding(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    canonical_boundary = (
        "def solve() -> int:\n"
        "    raise NotImplementedError('student boundary')\n\n"
        "def _completed_solve() -> int:\n"
        "    return 1\n\n"
    )
    rebindings = {
        "assignment": "solve = _completed_solve\n",
        "deletion": "del solve\n",
        "duplicate function": "def solve() -> int:\n    return 1\n",
        "import": "from completed import solve\n",
        "aliased import": "import completed as solve\n",
    }

    for label, rebinding in rebindings.items():
        starter.write_text(canonical_boundary + rebinding, encoding="utf-8")
        assert reachable_not_implemented_functions(starter) == (), label


def test_reachability_check_ignores_bindings_before_the_final_boundary(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    starter.write_text(
        "def _completed_solve() -> int:\n"
        "    return 1\n\n"
        "solve = _completed_solve\n"
        "del solve\n"
        "from completed import solve\n"
        'globals()["solve"] = _completed_solve\n\n'
        "def solve() -> int:\n"
        "    raise NotImplementedError('student boundary')\n",
        encoding="utf-8",
    )

    assert reachable_not_implemented_functions(starter) == ("solve",)


def test_reachability_check_rejects_class_scope_rebinding(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    starter.write_text(
        "def _completed_solve(self) -> int:\n"
        "    return 1\n\n"
        "class Solver:\n"
        "    def solve(self) -> int:\n"
        "        raise NotImplementedError('student boundary')\n\n"
        "    solve = _completed_solve\n",
        encoding="utf-8",
    )

    assert reachable_not_implemented_functions(starter) == ()


def test_reachability_check_rejects_outer_owner_rebinding(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    nested_boundary = (
        "def retry():\n"
        "    def decorate():\n"
        "        def wrapped() -> int:\n"
        "            raise NotImplementedError('student boundary')\n"
        "        return wrapped\n"
        "    return decorate\n\n"
        "def _completed_retry():\n"
        "    return lambda: 1\n\n"
    )
    starter.write_text(nested_boundary + "retry = _completed_retry\n", encoding="utf-8")

    assert reachable_not_implemented_functions(starter) == ()

    starter.write_text(
        "def _completed_retry():\n"
        "    return lambda: 1\n\n"
        "retry = _completed_retry\n\n"
        "def retry():\n"
        "    def decorate():\n"
        "        def wrapped() -> int:\n"
        "            raise NotImplementedError('student boundary')\n"
        "        return wrapped\n"
        "    return decorate\n",
        encoding="utf-8",
    )

    assert reachable_not_implemented_functions(starter) == ("retry.decorate.wrapped",)


def test_reachability_check_rejects_module_class_attribute_rebinding(tmp_path: Path) -> None:
    starter = tmp_path / "starter.py"
    class_boundary = (
        "class Solver:\n"
        "    def solve(self) -> int:\n"
        "        raise NotImplementedError('student boundary')\n\n"
        "def _completed_solve(self) -> int:\n"
        "    return 1\n\n"
    )
    rebindings = {
        "attribute assignment": "Solver.solve = _completed_solve\n",
        "literal setattr": 'setattr(Solver, "solve", _completed_solve)\n',
    }

    for label, rebinding in rebindings.items():
        starter.write_text(class_boundary + rebinding, encoding="utf-8")
        assert reachable_not_implemented_functions(starter) == (), label
