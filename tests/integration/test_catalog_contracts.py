"""Cross-repository curriculum catalog and progress contracts."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from roadmap_tools.catalog import Catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "identifier",
    [
        "data-paired-model-comparison",
        "data-randomized-experiment",
        "ml-knn-mechanics",
        "ml-tabular-study",
        "data-release-study",
        "ml-evaluation-case",
        "production-product-study",
        "rag-ranking-study",
        "ml-forecasting-intro",
        "python-interview-patterns",
        "backend-analytics-sql",
        "python-control-flow",
        "data-experiment-design",
        "ml-representation-study",
        "ml-bias-slices",
        "backend-sql-foundations",
    ],
)
def test_new_base_exercises_block_network(identifier: str, tmp_path: Path) -> None:
    """An accidental network call in any new base exercise fails visibly."""
    item = Catalog.load(REPOSITORY_ROOT).get(identifier)
    guard = item.readme.parent / "conftest.py"
    assert guard.is_file(), f"Missing offline fixture for {identifier}"
    (tmp_path / "conftest.py").write_bytes(guard.read_bytes())
    (tmp_path / "test_offline.py").write_text(
        "import socket\nimport pytest\n"
        "def test_socket_entry_points():\n"
        "    with pytest.raises((AssertionError, RuntimeError), match='(?i)offline'):\n"
        "        socket.create_connection(None)\n"
        "    with socket.socket() as connection:\n"
        "        with pytest.raises((AssertionError, RuntimeError), match='(?i)offline'):\n"
        "            connection.connect(None)\n"
        "        with pytest.raises((AssertionError, RuntimeError), match='(?i)offline'):\n"
        "            connection.connect_ex(None)\n",
        encoding="utf-8",
    )
    # Invalid addresses cannot open a real connection even if the guard is removed.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(tmp_path / "test_offline.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@dataclass(frozen=True)
class ExpectedItem:
    """One curriculum item in its exact learner-facing order."""

    identifier: str
    kind: str
    readme: str
    tests: tuple[str, ...]


def item(
    identifier: str,
    kind: str,
    readme: str,
    *tests: str,
) -> ExpectedItem:
    """Build a compact expected catalog record."""

    return ExpectedItem(identifier, kind, readme, tests)


EXPECTED_CATALOG = (
    item(
        "python-environment",
        "lesson",
        "modules/01_python_core/00_environment/README.md",
        "modules/01_python_core/tests/test_examples.py",
    ),
    item(
        "python-object-model",
        "lesson",
        "modules/01_python_core/01_object_model/README.md",
        "modules/01_python_core/tests/test_examples.py",
    ),
    item(
        "python-collections",
        "lesson",
        "modules/01_python_core/02_collections/README.md",
        "modules/01_python_core/02_collections",
    ),
    item(
        "python-detect-duplicates",
        "exercise",
        "modules/01_python_core/02_collections/exercises/detect_duplicates/README.md",
        "modules/01_python_core/02_collections/exercises/detect_duplicates/test_starter.py",
    ),
    item(
        "python-group-by-user",
        "exercise",
        "modules/01_python_core/02_collections/exercises/group_by_user/README.md",
        "modules/01_python_core/02_collections/exercises/group_by_user/test_starter.py",
    ),
    item(
        "python-provider-frequency",
        "exercise",
        "modules/01_python_core/02_collections/exercises/provider_frequency/README.md",
        "modules/01_python_core/02_collections/exercises/provider_frequency/test_starter.py",
    ),
    item(
        "python-sort-payments",
        "exercise",
        "modules/01_python_core/02_collections/exercises/sort_payments/README.md",
        "modules/01_python_core/02_collections/exercises/sort_payments/test_starter.py",
    ),
    item(
        "python-filter-project-events",
        "exercise",
        "modules/01_python_core/02_collections/exercises/filter_project_events/README.md",
        "modules/01_python_core/02_collections/exercises/filter_project_events/test_starter.py",
    ),
    item(
        "python-slice-windows",
        "exercise",
        "modules/01_python_core/02_collections/exercises/slice_windows/README.md",
        "modules/01_python_core/02_collections/exercises/slice_windows/test_starter.py",
    ),
    item(
        "python-unpack-settlements",
        "exercise",
        "modules/01_python_core/02_collections/exercises/unpack_settlements/README.md",
        "modules/01_python_core/02_collections/exercises/unpack_settlements/test_starter.py",
    ),
    item(
        "python-review-java-shaped-grouping",
        "exercise",
        "modules/01_python_core/02_collections/code_review/java_shaped_grouping/README.md",
        "modules/01_python_core/02_collections/code_review/java_shaped_grouping/test_characterization.py",
    ),
    item(
        "python-functions",
        "lesson",
        "modules/01_python_core/03_functions/README.md",
        "modules/01_python_core/03_functions",
    ),
    item(
        "python-configurable-filter",
        "exercise",
        "modules/01_python_core/03_functions/exercises/configurable_filter/README.md",
        "modules/01_python_core/03_functions/exercises/configurable_filter/test_starter.py",
    ),
    item(
        "python-combine-responses",
        "exercise",
        "modules/01_python_core/03_functions/exercises/combine_responses/README.md",
        "modules/01_python_core/03_functions/exercises/combine_responses/test_starter.py",
    ),
    item(
        "python-debug-mutable-defaults",
        "exercise",
        "modules/01_python_core/03_functions/debugging/mutable_defaults/README.md",
        "modules/01_python_core/03_functions/debugging/mutable_defaults/test_behavior.py",
    ),
    item(
        "python-review-stateful-report",
        "exercise",
        "modules/01_python_core/03_functions/code_review/stateful_report/README.md",
        "modules/01_python_core/03_functions/code_review/stateful_report/test_characterization.py",
    ),
    item(
        "python-typing",
        "lesson",
        "modules/01_python_core/04_typing/README.md",
        "modules/01_python_core/04_typing",
    ),
    item(
        "python-payment-processor-protocol",
        "exercise",
        "modules/01_python_core/04_typing/exercises/payment_processor_protocol/README.md",
        "modules/01_python_core/04_typing/exercises/payment_processor_protocol/test_starter.py",
    ),
    item(
        "python-transaction-report",
        "exercise",
        "modules/01_python_core/mini_features/transaction_report/README.md",
        "modules/01_python_core/mini_features/transaction_report/test_report.py",
    ),
    item(
        "python-data-modeling",
        "lesson",
        "modules/01_python_core/05_data_modeling/README.md",
        "modules/01_python_core/05_data_modeling",
    ),
    item(
        "python-payment-model",
        "exercise",
        "modules/01_python_core/05_data_modeling/exercises/payment_model/README.md",
        "modules/01_python_core/05_data_modeling/exercises/payment_model/test_starter.py",
    ),
    item(
        "python-io",
        "lesson",
        "modules/01_python_core/06_exceptions_io/README.md",
        "modules/01_python_core/06_exceptions_io",
    ),
    item(
        "python-json-export",
        "exercise",
        "modules/01_python_core/06_exceptions_io/exercises/json_export/README.md",
        "modules/01_python_core/06_exceptions_io/exercises/json_export/test_starter.py",
    ),
    item(
        "python-generators",
        "lesson",
        "modules/01_python_core/07_iterators_generators/README.md",
        "modules/01_python_core/07_iterators_generators",
    ),
    item(
        "python-debug-iterator-exhaustion",
        "exercise",
        "modules/01_python_core/07_iterators_generators/debugging/iterator_exhaustion/README.md",
        "modules/01_python_core/07_iterators_generators/debugging/iterator_exhaustion/test_behavior.py",
    ),
    item(
        "python-stream-transactions",
        "exercise",
        "modules/01_python_core/07_iterators_generators/exercises/stream_transactions/README.md",
        "modules/01_python_core/07_iterators_generators/exercises/stream_transactions/test_starter.py",
    ),
    item(
        "python-decorators",
        "lesson",
        "modules/01_python_core/08_decorators/README.md",
        "modules/01_python_core/08_decorators",
    ),
    item(
        "python-retry-gateway",
        "exercise",
        "modules/01_python_core/08_decorators/exercises/retry_gateway/README.md",
        "modules/01_python_core/08_decorators/exercises/retry_gateway/test_starter.py",
    ),
    item(
        "python-testing",
        "lesson",
        "modules/01_python_core/09_testing/README.md",
        "modules/01_python_core/09_testing",
    ),
    item(
        "python-mock-provider",
        "exercise",
        "modules/01_python_core/09_testing/exercises/mock_provider/README.md",
        "modules/01_python_core/09_testing/exercises/mock_provider/test_starter.py",
    ),
    item(
        "python-asyncio",
        "lesson",
        "modules/01_python_core/10_asyncio/README.md",
        "modules/01_python_core/10_asyncio",
    ),
    item(
        "python-fetch-quotes",
        "exercise",
        "modules/01_python_core/10_asyncio/exercises/fetch_quotes/README.md",
        "modules/01_python_core/10_asyncio/exercises/fetch_quotes/test_starter.py",
    ),
    item(
        "python-calendar-intervals",
        "exercise",
        "modules/01_python_core/exercises/calendar_intervals/README.md",
        "modules/01_python_core/exercises/calendar_intervals/test_starter.py",
    ),
    item(
        "python-word-index",
        "exercise",
        "modules/01_python_core/exercises/word_index/README.md",
        "modules/01_python_core/exercises/word_index/test_starter.py",
    ),
    item(
        "python-paged-stream",
        "exercise",
        "modules/01_python_core/exercises/paged_stream/README.md",
        "modules/01_python_core/exercises/paged_stream/test_starter.py",
    ),
    item(
        "python-bounded-fetch",
        "exercise",
        "modules/01_python_core/exercises/bounded_fetch/README.md",
        "modules/01_python_core/exercises/bounded_fetch/test_starter.py",
    ),
    item(
        "backend-fastapi",
        "lesson",
        "modules/02_python_backend/01_fastapi/README.md",
        "modules/02_python_backend/examples/support_api/test_app.py",
    ),
    item(
        "backend-pydantic",
        "lesson",
        "modules/02_python_backend/02_pydantic/README.md",
        "modules/02_python_backend/02_pydantic",
    ),
    item(
        "backend-transaction-contract",
        "exercise",
        "modules/02_python_backend/02_pydantic/exercises/transaction_contract/README.md",
        "modules/02_python_backend/02_pydantic/exercises/transaction_contract/test_starter.py",
    ),
    item(
        "backend-architecture",
        "lesson",
        "modules/02_python_backend/03_architecture_dependencies/README.md",
        "modules/02_python_backend/03_architecture_dependencies",
    ),
    item(
        "backend-payment-router",
        "exercise",
        "modules/02_python_backend/03_architecture_dependencies/exercises/payment_router/README.md",
        "modules/02_python_backend/03_architecture_dependencies/exercises/payment_router/test_starter.py",
    ),
    item(
        "backend-config-errors",
        "lesson",
        "modules/02_python_backend/04_config_errors_logging/README.md",
        "modules/02_python_backend/04_config_errors_logging",
    ),
    item(
        "backend-error-mapping",
        "exercise",
        "modules/02_python_backend/04_config_errors_logging/exercises/error_mapping/README.md",
        "modules/02_python_backend/04_config_errors_logging/exercises/error_mapping/test_starter.py",
    ),
    item(
        "backend-async",
        "lesson",
        "modules/02_python_backend/05_async_endpoints/README.md",
        "modules/02_python_backend/05_async_endpoints",
    ),
    item(
        "backend-provider-fanout",
        "exercise",
        "modules/02_python_backend/05_async_endpoints/exercises/provider_fanout/README.md",
        "modules/02_python_backend/05_async_endpoints/exercises/provider_fanout/test_starter.py",
    ),
    item(
        "backend-sqlalchemy",
        "lesson",
        "modules/02_python_backend/06_sqlalchemy/README.md",
        "modules/02_python_backend/06_sqlalchemy",
    ),
    item(
        "backend-transaction-repository",
        "exercise",
        "modules/02_python_backend/06_sqlalchemy/exercises/transaction_repository/README.md",
        "modules/02_python_backend/06_sqlalchemy/exercises/transaction_repository/test_starter.py",
    ),
    item(
        "backend-postgresql",
        "lesson",
        "modules/02_python_backend/07_postgresql/README.md",
        "modules/02_python_backend/07_postgresql",
    ),
    item(
        "backend-postgres-query",
        "exercise",
        "modules/02_python_backend/07_postgresql/exercises/postgres_query/README.md",
        "modules/02_python_backend/07_postgresql/exercises/postgres_query/test_starter.py",
    ),
    item(
        "backend-testing",
        "lesson",
        "modules/02_python_backend/08_api_integration_testing/README.md",
        "modules/02_python_backend/08_api_integration_testing",
    ),
    item(
        "backend-api-test-review",
        "exercise",
        "modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/README.md",
        "modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/test_characterization.py",
    ),
    item(
        "backend-docker",
        "lesson",
        "modules/02_python_backend/09_docker_delivery/README.md",
        "modules/02_python_backend/tests/test_lesson_contracts.py",
    ),
    item(
        "backend-library-search",
        "exercise",
        "modules/02_python_backend/exercises/library_search/README.md",
        "modules/02_python_backend/exercises/library_search/test_starter.py",
    ),
    item(
        "backend-room-booking-api",
        "exercise",
        "modules/02_python_backend/exercises/room_booking_api/README.md",
        "modules/02_python_backend/exercises/room_booking_api/test_starter.py",
    ),
    item(
        "backend-conditional-cache",
        "exercise",
        "modules/02_python_backend/exercises/conditional_cache/README.md",
        "modules/02_python_backend/exercises/conditional_cache/test_starter.py",
    ),
    item(
        "backend-equipment-repository",
        "exercise",
        "modules/02_python_backend/exercises/equipment_repository/README.md",
        "modules/02_python_backend/exercises/equipment_repository/test_starter.py",
    ),
    item(
        "data-numpy",
        "lesson",
        "modules/03_data_foundations/01_numpy/README.md",
        "modules/03_data_foundations/01_numpy",
    ),
    item(
        "data-payment-matrix",
        "exercise",
        "modules/03_data_foundations/01_numpy/exercises/payment_matrix/README.md",
        "modules/03_data_foundations/01_numpy/exercises/payment_matrix/test_starter.py",
    ),
    item(
        "data-pandas",
        "lesson",
        "modules/03_data_foundations/02_pandas_core/README.md",
        "modules/03_data_foundations/02_pandas_core",
    ),
    item(
        "data-transaction-summary",
        "exercise",
        "modules/03_data_foundations/02_pandas_core/exercises/transaction_summary/README.md",
        "modules/03_data_foundations/02_pandas_core/exercises/transaction_summary/test_starter.py",
    ),
    item(
        "data-merchant-join",
        "exercise",
        "modules/03_data_foundations/02_pandas_core/exercises/merchant_join/README.md",
        "modules/03_data_foundations/02_pandas_core/exercises/merchant_join/test_starter.py",
    ),
    item(
        "data-quality",
        "lesson",
        "modules/03_data_foundations/03_data_quality/README.md",
        "modules/03_data_foundations/03_data_quality",
    ),
    item(
        "data-quality-report",
        "exercise",
        "modules/03_data_foundations/03_data_quality/exercises/quality_report/README.md",
        "modules/03_data_foundations/03_data_quality/exercises/quality_report/test_starter.py",
    ),
    item(
        "data-statistics",
        "lesson",
        "modules/03_data_foundations/04_practical_statistics/README.md",
        "modules/03_data_foundations/04_practical_statistics",
    ),
    item(
        "data-statistical-profile",
        "exercise",
        "modules/03_data_foundations/04_practical_statistics/exercises/statistical_profile/README.md",
        "modules/03_data_foundations/04_practical_statistics/exercises/statistical_profile/test_starter.py",
    ),
    item(
        "data-bayes-alert",
        "exercise",
        "modules/03_data_foundations/04_practical_statistics/exercises/bayes_alert/README.md",
        "modules/03_data_foundations/04_practical_statistics/exercises/bayes_alert/test_starter.py",
    ),
    item(
        "data-splits",
        "lesson",
        "modules/03_data_foundations/05_splits_and_leakage/README.md",
        "modules/03_data_foundations/05_splits_and_leakage",
    ),
    item(
        "data-time-split",
        "exercise",
        "modules/03_data_foundations/05_splits_and_leakage/exercises/time_split/README.md",
        "modules/03_data_foundations/05_splits_and_leakage/exercises/time_split/test_starter.py",
    ),
    item(
        "data-fraud-metrics",
        "lesson",
        "modules/03_data_foundations/06_fraud_metrics/README.md",
        "modules/03_data_foundations/06_fraud_metrics",
    ),
    item(
        "data-confusion-metrics",
        "exercise",
        "modules/03_data_foundations/06_fraud_metrics/exercises/confusion_metrics/README.md",
        "modules/03_data_foundations/06_fraud_metrics/exercises/confusion_metrics/test_starter.py",
    ),
    item(
        "data-ranking-metrics",
        "exercise",
        "modules/03_data_foundations/06_fraud_metrics/exercises/ranking_metrics/README.md",
        "modules/03_data_foundations/06_fraud_metrics/exercises/ranking_metrics/test_starter.py",
    ),
    item(
        "data-weather-quality",
        "exercise",
        "modules/03_data_foundations/exercises/weather_quality/README.md",
        "modules/03_data_foundations/exercises/weather_quality/test_starter.py",
    ),
    item(
        "data-image-pooling",
        "exercise",
        "modules/03_data_foundations/exercises/image_pooling/README.md",
        "modules/03_data_foundations/exercises/image_pooling/test_starter.py",
    ),
    item(
        "data-library-joins",
        "exercise",
        "modules/03_data_foundations/exercises/library_joins/README.md",
        "modules/03_data_foundations/exercises/library_joins/test_starter.py",
    ),
    item(
        "data-paired-observations",
        "exercise",
        "modules/03_data_foundations/exercises/paired_observations/README.md",
        "modules/03_data_foundations/exercises/paired_observations/test_starter.py",
    ),
    item(
        "data-paired-model-comparison",
        "exercise",
        "modules/03_data_foundations/exercises/paired_model_comparison/README.md",
        "modules/03_data_foundations/exercises/paired_model_comparison/test_starter.py",
        "modules/03_data_foundations/exercises/paired_model_comparison/test_evidence.py",
        "modules/03_data_foundations/exercises/paired_model_comparison/test_example.py",
    ),
    item(
        "data-randomized-experiment",
        "exercise",
        "modules/03_data_foundations/exercises/randomized_experiment/README.md",
        "modules/03_data_foundations/exercises/randomized_experiment/test_starter.py",
        "modules/03_data_foundations/exercises/randomized_experiment/test_example.py",
    ),
    item(
        "ml-problem-framing",
        "lesson",
        "modules/04_machine_learning/01_problem_framing/README.md",
        "modules/04_machine_learning/01_problem_framing",
    ),
    item(
        "ml-validation",
        "lesson",
        "modules/04_machine_learning/02_validation/README.md",
        "modules/04_machine_learning/02_validation",
    ),
    item(
        "ml-group-safe-split",
        "exercise",
        "modules/04_machine_learning/02_validation/exercises/group_safe_split/README.md",
        "modules/04_machine_learning/02_validation/exercises/group_safe_split/test_starter.py",
    ),
    item(
        "ml-preprocessing",
        "lesson",
        "modules/04_machine_learning/03_preprocessing/README.md",
        "modules/04_machine_learning/03_preprocessing",
    ),
    item(
        "ml-mixed-feature-pipeline",
        "exercise",
        "modules/04_machine_learning/03_preprocessing/exercises/mixed_feature_pipeline/README.md",
        "modules/04_machine_learning/03_preprocessing/exercises/mixed_feature_pipeline/test_starter.py",
    ),
    item(
        "ml-models",
        "lesson",
        "modules/04_machine_learning/04_models/README.md",
        "modules/04_machine_learning/04_models",
    ),
    item(
        "ml-model-comparison",
        "exercise",
        "modules/04_machine_learning/04_models/exercises/model_comparison/README.md",
        "modules/04_machine_learning/04_models/exercises/model_comparison/test_starter.py",
    ),
    item(
        "ml-evaluation",
        "lesson",
        "modules/04_machine_learning/05_evaluation/README.md",
        "modules/04_machine_learning/05_evaluation",
    ),
    item(
        "ml-reproducibility",
        "lesson",
        "modules/04_machine_learning/06_reproducibility/README.md",
        "modules/04_machine_learning/06_reproducibility",
    ),
    item(
        "ml-evaluation-report",
        "exercise",
        "modules/04_machine_learning/06_reproducibility/exercises/evaluation_report/README.md",
        "modules/04_machine_learning/06_reproducibility/exercises/evaluation_report/test_starter.py",
    ),
    item(
        "ml-time-series-split",
        "exercise",
        "modules/04_machine_learning/exercises/time_series_split/README.md",
        "modules/04_machine_learning/exercises/time_series_split/test_starter.py",
    ),
    item(
        "ml-multiclass-report",
        "exercise",
        "modules/04_machine_learning/exercises/multiclass_report/README.md",
        "modules/04_machine_learning/exercises/multiclass_report/test_starter.py",
    ),
    item(
        "ml-threshold-policy",
        "exercise",
        "modules/04_machine_learning/exercises/threshold_policy/README.md",
        "modules/04_machine_learning/exercises/threshold_policy/test_starter.py",
    ),
    item(
        "llm-interfaces",
        "lesson",
        "modules/05_llm_engineering/01_llm_interfaces/README.md",
        "modules/05_llm_engineering/tests/test_examples.py",
    ),
    item(
        "llm-prompt-contracts",
        "lesson",
        "modules/05_llm_engineering/02_prompt_contracts/README.md",
        "modules/05_llm_engineering/tests/test_examples.py",
    ),
    item(
        "llm-prompt-messages",
        "exercise",
        "modules/05_llm_engineering/02_prompt_contracts/exercises/prompt_messages/README.md",
        "modules/05_llm_engineering/02_prompt_contracts/exercises/prompt_messages/test_starter.py",
    ),
    item(
        "llm-structured-outputs",
        "lesson",
        "modules/05_llm_engineering/03_structured_outputs/README.md",
        "modules/05_llm_engineering/tests/test_examples.py",
    ),
    item(
        "llm-event-contract",
        "exercise",
        "modules/05_llm_engineering/03_structured_outputs/exercises/event_contract/README.md",
        "modules/05_llm_engineering/03_structured_outputs/exercises/event_contract/test_starter.py",
    ),
    item(
        "llm-context-cost",
        "lesson",
        "modules/05_llm_engineering/04_context_and_cost/README.md",
        "modules/05_llm_engineering/tests/test_examples.py",
    ),
    item(
        "llm-context-budget",
        "exercise",
        "modules/05_llm_engineering/04_context_and_cost/exercises/context_budget/README.md",
        "modules/05_llm_engineering/04_context_and_cost/exercises/context_budget/test_starter.py",
    ),
    item(
        "llm-evaluation",
        "lesson",
        "modules/05_llm_engineering/05_evaluation/README.md",
        "modules/05_llm_engineering/tests/test_examples.py",
    ),
    item(
        "llm-answer-evaluation",
        "exercise",
        "modules/05_llm_engineering/05_evaluation/exercises/answer_evaluation/README.md",
        "modules/05_llm_engineering/05_evaluation/exercises/answer_evaluation/test_starter.py",
    ),
    item(
        "llm-reliability-tools",
        "lesson",
        "modules/05_llm_engineering/06_reliability_and_tools/README.md",
        "modules/05_llm_engineering/tests/test_examples.py",
    ),
    item(
        "llm-bounded-retry",
        "exercise",
        "modules/05_llm_engineering/06_reliability_and_tools/exercises/bounded_retry/README.md",
        "modules/05_llm_engineering/06_reliability_and_tools/exercises/bounded_retry/test_starter.py",
    ),
    item(
        "llm-context-packing",
        "exercise",
        "modules/05_llm_engineering/exercises/context_packing/README.md",
        "modules/05_llm_engineering/exercises/context_packing/test_starter.py",
    ),
    item(
        "llm-response-cache",
        "exercise",
        "modules/05_llm_engineering/exercises/response_cache/README.md",
        "modules/05_llm_engineering/exercises/response_cache/test_starter.py",
    ),
    item(
        "llm-stream-assembly",
        "exercise",
        "modules/05_llm_engineering/exercises/stream_assembly/README.md",
        "modules/05_llm_engineering/exercises/stream_assembly/test_starter.py",
    ),
    item(
        "rag-contracts",
        "lesson",
        "modules/06_rag/01_retrieval_contracts/README.md",
        "modules/06_rag/01_retrieval_contracts",
    ),
    item(
        "rag-ingestion",
        "lesson",
        "modules/06_rag/02_ingestion_chunking/README.md",
        "modules/06_rag/02_ingestion_chunking",
    ),
    item(
        "rag-text-chunking",
        "exercise",
        "modules/06_rag/exercises/text_chunking/README.md",
        "modules/06_rag/exercises/text_chunking/test_starter.py",
    ),
    item(
        "rag-retrieval",
        "lesson",
        "modules/06_rag/03_lexical_dense_retrieval/README.md",
        "modules/06_rag/03_lexical_dense_retrieval",
    ),
    item(
        "rag-vector-search",
        "exercise",
        "modules/06_rag/03_lexical_dense_retrieval/exercises/vector_search/README.md",
        "modules/06_rag/03_lexical_dense_retrieval/exercises/vector_search/test_starter.py",
    ),
    item(
        "rag-hybrid",
        "lesson",
        "modules/06_rag/04_hybrid_reranking/README.md",
        "modules/06_rag/04_hybrid_reranking",
    ),
    item(
        "rag-rank-fusion",
        "exercise",
        "modules/06_rag/04_hybrid_reranking/exercises/reciprocal_rank_fusion/README.md",
        "modules/06_rag/04_hybrid_reranking/exercises/reciprocal_rank_fusion/test_starter.py",
    ),
    item(
        "rag-grounding",
        "lesson",
        "modules/06_rag/05_grounded_answers/README.md",
        "modules/06_rag/05_grounded_answers",
    ),
    item(
        "rag-citation-validation",
        "exercise",
        "modules/06_rag/05_grounded_answers/exercises/citation_validation/README.md",
        "modules/06_rag/05_grounded_answers/exercises/citation_validation/test_starter.py",
    ),
    item(
        "rag-evaluation",
        "lesson",
        "modules/06_rag/06_rag_evaluation/README.md",
        "modules/06_rag/06_rag_evaluation",
    ),
    item(
        "rag-retrieval-evaluation",
        "exercise",
        "modules/06_rag/06_rag_evaluation/exercises/retrieval_evaluation/README.md",
        "modules/06_rag/06_rag_evaluation/exercises/retrieval_evaluation/test_starter.py",
    ),
    item(
        "rag-index-sync",
        "exercise",
        "modules/06_rag/exercises/index_sync/README.md",
        "modules/06_rag/exercises/index_sync/test_starter.py",
    ),
    item(
        "rag-context-diversity",
        "exercise",
        "modules/06_rag/exercises/context_diversity/README.md",
        "modules/06_rag/exercises/context_diversity/test_starter.py",
    ),
    item(
        "rag-retrieval-regression",
        "exercise",
        "modules/06_rag/exercises/retrieval_regression/README.md",
        "modules/06_rag/exercises/retrieval_regression/test_starter.py",
    ),
    item(
        "agents-state",
        "lesson",
        "modules/07_agents/01_workflows_state/README.md",
        "modules/07_agents/tests/test_examples.py",
    ),
    item(
        "agents-workflow-schedule",
        "exercise",
        "modules/07_agents/exercises/workflow_schedule/README.md",
        "modules/07_agents/exercises/workflow_schedule/test_starter.py",
    ),
    item(
        "agents-tools",
        "lesson",
        "modules/07_agents/02_tools_permissions/README.md",
        "modules/07_agents/tests/test_examples.py",
    ),
    item(
        "agents-tool-dispatch",
        "exercise",
        "modules/07_agents/02_tools_permissions/exercises/tool_dispatch/README.md",
        "modules/07_agents/02_tools_permissions/exercises/tool_dispatch/test_starter.py",
    ),
    item(
        "agents-loop",
        "lesson",
        "modules/07_agents/03_bounded_agents/README.md",
        "modules/07_agents/tests/test_examples.py",
    ),
    item(
        "agents-bounded-loop",
        "exercise",
        "modules/07_agents/03_bounded_agents/exercises/bounded_loop/README.md",
        "modules/07_agents/03_bounded_agents/exercises/bounded_loop/test_starter.py",
    ),
    item(
        "agents-checkpoints",
        "lesson",
        "modules/07_agents/04_checkpoints_approvals/README.md",
        "modules/07_agents/tests/test_examples.py",
    ),
    item(
        "agents-checkpoint-resume",
        "exercise",
        "modules/07_agents/04_checkpoints_approvals/exercises/checkpoint_resume/README.md",
        "modules/07_agents/04_checkpoints_approvals/exercises/checkpoint_resume/test_starter.py",
    ),
    item(
        "agents-langgraph-mcp",
        "lesson",
        "modules/07_agents/05_langgraph_mcp/README.md",
        "modules/07_agents/tests/test_examples.py",
    ),
    item(
        "agents-evaluation",
        "lesson",
        "modules/07_agents/06_evaluation_handoffs/README.md",
        "modules/07_agents/tests/test_examples.py",
    ),
    item(
        "agents-trace-evaluation",
        "exercise",
        "modules/07_agents/06_evaluation_handoffs/exercises/trace_evaluation/README.md",
        "modules/07_agents/06_evaluation_handoffs/exercises/trace_evaluation/test_starter.py",
    ),
    item(
        "agents-plan-validation",
        "exercise",
        "modules/07_agents/exercises/plan_validation/README.md",
        "modules/07_agents/exercises/plan_validation/test_starter.py",
    ),
    item(
        "agents-handoff-packet",
        "exercise",
        "modules/07_agents/exercises/handoff_packet/README.md",
        "modules/07_agents/exercises/handoff_packet/test_starter.py",
    ),
    item(
        "agents-tool-result-routing",
        "exercise",
        "modules/07_agents/exercises/tool_result_routing/README.md",
        "modules/07_agents/exercises/tool_result_routing/test_starter.py",
    ),
    item(
        "production-serving",
        "lesson",
        "modules/08_production_ai/01_serving_contracts/README.md",
        "modules/08_production_ai/01_serving_contracts/test_example.py",
    ),
    item(
        "production-releases",
        "lesson",
        "modules/08_production_ai/02_releases_evaluation/README.md",
        "modules/08_production_ai/02_releases_evaluation/test_example.py",
    ),
    item(
        "production-release-gate",
        "exercise",
        "modules/08_production_ai/02_releases_evaluation/exercises/release_gate/README.md",
        "modules/08_production_ai/02_releases_evaluation/exercises/release_gate/test_starter.py",
    ),
    item(
        "production-observability",
        "lesson",
        "modules/08_production_ai/03_observability/README.md",
        "modules/08_production_ai/03_observability/test_example.py",
    ),
    item(
        "production-request-metrics",
        "exercise",
        "modules/08_production_ai/exercises/request_metrics/README.md",
        "modules/08_production_ai/exercises/request_metrics/test_starter.py",
    ),
    item(
        "production-resilience",
        "lesson",
        "modules/08_production_ai/04_budgets_resilience/README.md",
        "modules/08_production_ai/04_budgets_resilience/test_example.py",
    ),
    item(
        "production-budget-reservation",
        "exercise",
        "modules/08_production_ai/04_budgets_resilience/exercises/budget_reservation/README.md",
        "modules/08_production_ai/04_budgets_resilience/exercises/budget_reservation/test_starter.py",
    ),
    item(
        "production-privacy",
        "lesson",
        "modules/08_production_ai/05_privacy_security/README.md",
        "modules/08_production_ai/05_privacy_security/test_example.py",
    ),
    item(
        "production-redact-events",
        "exercise",
        "modules/08_production_ai/05_privacy_security/exercises/redact_events/README.md",
        "modules/08_production_ai/05_privacy_security/exercises/redact_events/test_starter.py",
    ),
    item(
        "production-rollout",
        "lesson",
        "modules/08_production_ai/06_rollout_incidents/README.md",
        "modules/08_production_ai/06_rollout_incidents/test_example.py",
    ),
    item(
        "production-rollout-decision",
        "exercise",
        "modules/08_production_ai/06_rollout_incidents/exercises/rollout_decision/README.md",
        "modules/08_production_ai/06_rollout_incidents/exercises/rollout_decision/test_starter.py",
    ),
    item(
        "production-artifact-manifest",
        "exercise",
        "modules/08_production_ai/exercises/artifact_manifest/README.md",
        "modules/08_production_ai/exercises/artifact_manifest/test_starter.py",
    ),
    item(
        "production-error-budget",
        "exercise",
        "modules/08_production_ai/exercises/error_budget/README.md",
        "modules/08_production_ai/exercises/error_budget/test_starter.py",
    ),
    item(
        "production-retention-policy",
        "exercise",
        "modules/08_production_ai/exercises/retention_policy/README.md",
        "modules/08_production_ai/exercises/retention_policy/test_starter.py",
    ),
    item(
        "banking-ai-lab",
        "project",
        "projects/banking_ai_lab/README.md",
        "projects/banking_ai_lab",
    ),
    item(
        "ml-training-bridge",
        "lesson",
        "modules/04_machine_learning/07_training_bridge/README.md",
        "modules/04_machine_learning/07_training_bridge/test_bridge.py",
    ),
    item(
        "ml-knn-mechanics",
        "exercise",
        "modules/04_machine_learning/exercises/knn_mechanics/README.md",
        "modules/04_machine_learning/exercises/knn_mechanics/test_starter.py",
        "modules/04_machine_learning/exercises/knn_mechanics/test_example.py",
    ),
    item(
        "ml-tabular-study",
        "exercise",
        "modules/04_machine_learning/exercises/tabular_study/README.md",
        "modules/04_machine_learning/exercises/tabular_study/test_starter.py",
        "modules/04_machine_learning/exercises/tabular_study/test_example.py",
        "modules/04_machine_learning/exercises/tabular_study/test_evidence.py",
    ),
    item(
        "lab-pytorch",
        "lab",
        "labs/01_pytorch_foundations/README.md",
        "labs/01_pytorch_foundations/test_example.py",
        "labs/01_pytorch_foundations/test_starter.py",
        "labs/01_pytorch_foundations/test_report.py",
    ),
    item(
        "lab-training-resume",
        "exercise",
        "labs/01_pytorch_foundations/exercises/resume_training/README.md",
        "labs/01_pytorch_foundations/exercises/resume_training/test_starter.py",
        "labs/01_pytorch_foundations/exercises/resume_training/test_evidence.py",
        "labs/01_pytorch_foundations/exercises/resume_training/test_smoke.py",
    ),
    item(
        "lab-huggingface",
        "lab",
        "labs/02_huggingface_models/README.md",
        "labs/02_huggingface_models/test_example.py",
        "labs/02_huggingface_models/test_starter.py",
        "labs/02_huggingface_models/test_protocol.py",
    ),
    item(
        "lab-attention-mechanics",
        "exercise",
        "labs/02_huggingface_models/attention_mechanics/README.md",
        "labs/02_huggingface_models/attention_mechanics/test_starter.py",
        "labs/02_huggingface_models/attention_mechanics/test_example.py",
    ),
    item(
        "lab-training-diagnostics",
        "exercise",
        "labs/01_pytorch_foundations/debugging/README.md",
        "labs/01_pytorch_foundations/debugging/test_starter.py",
        "labs/01_pytorch_foundations/debugging/test_cases.py",
        "labs/01_pytorch_foundations/debugging/test_evidence.py",
    ),
    item(
        "data-release-study",
        "exercise",
        "modules/03_data_foundations/exercises/data_release/README.md",
        "modules/03_data_foundations/exercises/data_release/test_starter.py",
        "modules/03_data_foundations/exercises/data_release/test_generate.py",
        "modules/03_data_foundations/exercises/data_release/test_evidence.py",
    ),
    item(
        "ml-evaluation-case",
        "exercise",
        "modules/04_machine_learning/exercises/evaluation_case/README.md",
        "modules/04_machine_learning/exercises/evaluation_case/test_starter.py",
        "modules/04_machine_learning/exercises/evaluation_case/test_case.py",
        "modules/04_machine_learning/exercises/evaluation_case/test_evidence.py",
        "tests/tooling/test_open_control_evidence.py",
    ),
    item(
        "production-product-study",
        "exercise",
        "modules/08_production_ai/exercises/product_study/README.md",
        "modules/08_production_ai/exercises/product_study/test_starter.py",
        "modules/08_production_ai/exercises/product_study/test_evidence.py",
        "tests/tooling/test_open_control_evidence.py",
    ),
    item(
        "rag-ranking-study",
        "exercise",
        "modules/06_rag/exercises/ranking_study/README.md",
        "modules/06_rag/exercises/ranking_study/test_starter.py",
        "modules/06_rag/exercises/ranking_study/test_evidence.py",
    ),
    item(
        "ml-forecasting-intro",
        "exercise",
        "modules/04_machine_learning/exercises/forecasting_intro/README.md",
        "modules/04_machine_learning/exercises/forecasting_intro/test_starter.py",
        "modules/04_machine_learning/exercises/forecasting_intro/test_example.py",
        "modules/04_machine_learning/exercises/forecasting_intro/test_evidence.py",
    ),
    item(
        "python-interview-patterns",
        "exercise",
        "modules/01_python_core/exercises/interview_patterns/README.md",
        "modules/01_python_core/exercises/interview_patterns/test_starter.py",
        "modules/01_python_core/exercises/interview_patterns/test_instrumentation.py",
    ),
    item(
        "backend-analytics-sql",
        "exercise",
        "modules/02_python_backend/exercises/analytics_sql/README.md",
        "modules/02_python_backend/exercises/analytics_sql/test_starter.py",
        "modules/02_python_backend/exercises/analytics_sql/test_queries.py",
    ),
    item(
        "document-a1-reproduction",
        "exercise",
        "projects/document_intelligence_lab/part_a1/exercise/README.md",
        "projects/document_intelligence_lab/part_a1/exercise/test_starter.py",
        "projects/document_intelligence_lab/part_a1/exercise/test_evidence.py",
    ),
    item(
        "python-control-flow",
        "exercise",
        "modules/01_python_core/00_environment/practice/README.md",
        "modules/01_python_core/00_environment/practice/test_starter.py",
    ),
    item(
        "data-experiment-design",
        "exercise",
        "modules/03_data_foundations/exercises/experiment_design/README.md",
        "modules/03_data_foundations/exercises/experiment_design/test_starter.py",
    ),
    item(
        "ml-representation-study",
        "exercise",
        "modules/04_machine_learning/exercises/representation_study/README.md",
        "modules/04_machine_learning/exercises/representation_study/test_starter.py",
    ),
    item(
        "ml-bias-slices",
        "exercise",
        "modules/04_machine_learning/exercises/bias_slices/README.md",
        "modules/04_machine_learning/exercises/bias_slices/test_starter.py",
    ),
    item(
        "backend-sql-foundations",
        "exercise",
        "modules/02_python_backend/exercises/sql_foundations/README.md",
        "modules/02_python_backend/exercises/sql_foundations/test_starter.py",
    ),
)

READINESS_CATALOG = (
    item(
        "ml-gradient-derivations",
        "exercise",
        "modules/04_machine_learning/exercises/gradient_derivations/README.md",
        "modules/04_machine_learning/exercises/gradient_derivations/test_starter.py",
    ),
    item(
        "ml-linear-geometry",
        "exercise",
        "modules/04_machine_learning/exercises/linear_geometry/README.md",
        "modules/04_machine_learning/exercises/linear_geometry/test_starter.py",
    ),
    item(
        "ml-tree-boosting",
        "exercise",
        "modules/04_machine_learning/exercises/tree_boosting/README.md",
        "modules/04_machine_learning/exercises/tree_boosting/test_starter.py",
    ),
    item(
        "data-training-stability",
        "exercise",
        "modules/03_data_foundations/exercises/training_stability/README.md",
        "modules/03_data_foundations/exercises/training_stability/test_starter.py",
    ),
    item(
        "python-async-lifecycle",
        "exercise",
        "modules/01_python_core/exercises/async_lifecycle/README.md",
        "modules/01_python_core/exercises/async_lifecycle/test_starter.py",
    ),
    item(
        "python-package-delivery",
        "exercise",
        "modules/01_python_core/exercises/package_delivery/README.md",
        "modules/01_python_core/exercises/package_delivery/test_starter.py",
    ),
    item(
        "backend-schema-migrations",
        "exercise",
        "modules/02_python_backend/exercises/schema_migrations/README.md",
        "modules/02_python_backend/exercises/schema_migrations/test_starter.py",
    ),
    item(
        "ml-external-tabular",
        "project",
        "projects/external_tabular/README.md",
        "projects/external_tabular/test_submission.py",
    ),
    item(
        "document-external-model-study",
        "project",
        "projects/document_intelligence_lab/external_model_study/README.md",
        "projects/document_intelligence_lab/external_model_study/test_submission.py",
    ),
    item(
        "rag-end-to-end-evaluation",
        "exercise",
        "labs/03_real_rag/end_to_end/README.md",
        "labs/03_real_rag/end_to_end/test_starter.py",
        "labs/03_real_rag/end_to_end/test_evidence.py",
    ),
    item(
        "production-service-lifecycle",
        "exercise",
        "projects/document_intelligence_lab/production_readiness/README.md",
        "projects/document_intelligence_lab/production_readiness/test_starter.py",
    ),
    item(
        "ml-data-pipeline",
        "exercise",
        "projects/document_intelligence_lab/data_pipeline/README.md",
        "projects/document_intelligence_lab/data_pipeline/test_starter.py",
    ),
)
READINESS_IDS = tuple(entry.identifier for entry in READINESS_CATALOG)
EXPECTED_CATALOG += READINESS_CATALOG

LESSON_IDS = tuple(entry.identifier for entry in EXPECTED_CATALOG if entry.kind == "lesson")
PROGRESS_IDS = (
    tuple(entry.identifier for entry in EXPECTED_CATALOG if entry.kind in {"lesson", "lab"})
    + READINESS_IDS
)
FIRST_SPRINT_IDS = (
    "python-detect-duplicates",
    "python-group-by-user",
    "python-provider-frequency",
    "python-sort-payments",
    "python-filter-project-events",
    "python-slice-windows",
    "python-unpack-settlements",
    "python-configurable-filter",
    "python-combine-responses",
    "python-payment-processor-protocol",
    "python-debug-mutable-defaults",
    "python-debug-iterator-exhaustion",
    "python-review-java-shaped-grouping",
    "python-review-stateful-report",
    "python-transaction-report",
)
LATER_PYTHON_PRACTICE_IDS = (
    "python-payment-model",
    "python-json-export",
    "python-stream-transactions",
    "python-retry-gateway",
    "python-mock-provider",
    "python-fetch-quotes",
)
BACKEND_EXERCISE_IDS = tuple(
    entry.identifier
    for entry in EXPECTED_CATALOG
    if entry.kind == "exercise" and entry.identifier.startswith("backend-")
)
DATA_EXERCISE_IDS = tuple(
    entry.identifier
    for entry in EXPECTED_CATALOG
    if entry.kind == "exercise" and entry.identifier.startswith("data-")
)


def expected_identifiers() -> tuple[str, ...]:
    """Return the stable catalog order; learning_tracks.toml defines study routes."""

    return tuple(entry.identifier for entry in EXPECTED_CATALOG)


def test_catalog_is_the_complete_ordered_roadmap() -> None:
    catalog = Catalog.load(REPOSITORY_ROOT)

    assert tuple(item.identifier for item in catalog.items) == expected_identifiers()
    assert tuple(item.kind for item in catalog.items) == tuple(
        entry.kind for entry in EXPECTED_CATALOG
    )
    assert len(catalog.items) == 180
    assert len(LESSON_IDS) == 57
    assert len(FIRST_SPRINT_IDS) == 15
    assert len(LATER_PYTHON_PRACTICE_IDS) == 6
    assert len(BACKEND_EXERCISE_IDS) == 14
    assert len(DATA_EXERCISE_IDS) == 18
    assert tuple(item.identifier for item in catalog.items if item.kind == "project") == (
        "banking-ai-lab",
        "ml-external-tabular",
        "document-external-model-study",
    )


def test_catalog_has_exact_readmes_real_test_targets_and_matching_titles() -> None:
    catalog = Catalog.load(REPOSITORY_ROOT)

    for expected in EXPECTED_CATALOG:
        actual = catalog.get(expected.identifier)
        assert actual.readme == (REPOSITORY_ROOT / expected.readme).resolve()
        assert actual.tests == tuple((REPOSITORY_ROOT / path).resolve() for path in expected.tests)
        assert actual.readme.is_file()
        heading = actual.readme.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")
        assert actual.title == heading
        for target in actual.tests:
            assert target.exists()
            assert (
                target.is_file() and target.suffix == ".py" and target.name.startswith("test")
            ) or (target.is_dir() and any(target.rglob("test_*.py")))


def test_catalog_contains_each_required_task_inventory_exactly_once() -> None:
    identifiers = expected_identifiers()

    for inventory in (
        FIRST_SPRINT_IDS,
        LATER_PYTHON_PRACTICE_IDS,
        BACKEND_EXERCISE_IDS,
        DATA_EXERCISE_IDS,
    ):
        assert len(inventory) == len(set(inventory))
        assert all(identifiers.count(identifier) == 1 for identifier in inventory)


def test_new_practices_do_not_expand_legacy_check_directories() -> None:
    catalog = Catalog.load(REPOSITORY_ROOT)
    new_ids = {
        "python-control-flow",
        "data-experiment-design",
        "ml-representation-study",
        "ml-bias-slices",
        "backend-sql-foundations",
        *READINESS_IDS,
    }
    for new_id in new_ids:
        new_tests = catalog.get(new_id).tests
        for legacy in catalog.items:
            if legacy.identifier in new_ids:
                continue
            for target in legacy.tests:
                assert all(
                    test != target and not (target.is_dir() and test.is_relative_to(target))
                    for test in new_tests
                ), f"{new_id} unexpectedly expands {legacy.identifier}"


def test_learning_cli_list_matches_the_catalog_order() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/learn.py", "list"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert tuple(line.split(" ", 1)[0] for line in result.stdout.splitlines()) == (
        expected_identifiers()
    )


def test_progress_and_status_cover_every_lesson_in_roadmap_order() -> None:
    progress_entries = tuple(
        line[6:]
        for line in (REPOSITORY_ROOT / "progress.md").read_text(encoding="utf-8").splitlines()
        if line.startswith(("- [ ] ", "- [~] ", "- [x] "))
    )
    assert progress_entries == PROGRESS_IDS

    result = subprocess.run(
        [sys.executable, "scripts/learn.py", "status"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert tuple(line[4:] for line in result.stdout.splitlines()) == PROGRESS_IDS
