# ruff: noqa: RUF001, RUF002
"""Самостоятельная dense-RAG реализация; author runtime.py изучайте после своей попытки."""

from typing import Any


def pool_tokens(hidden: Any, attention_mask: Any) -> Any:
    """Вернуть L2-нормированный masked mean [N,D]; нулевые маски отклонить."""
    raise NotImplementedError("Реализуйте masked mean с проверками формы и пустых масок")


def answer_case(
    case: dict[str, Any],
    chunks: tuple[Any, ...],
    vectors: Any,
    query_vector: Any,
    config: Any,
    generator: Any,
) -> dict[str, Any]:
    """Независимо реализовать контракт runtime.run_case, включая метрики и policy.

    Не импортировать run_case/rank как решение. Входные аннотации expected_answers,
    relevant_ids, should_abstain доступны только вычислению метрик после ответа.
    Доступ/актуальность — доверенные revoked_ids/stale_ids, а не gold kind.
    Полный формат результата задают README и runtime.run_case.
    """
    raise NotImplementedError("Соедините dense retrieval, доверенную policy и generator")
