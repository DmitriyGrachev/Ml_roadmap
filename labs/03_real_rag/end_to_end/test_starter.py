"""Learner behavioral checks; author demo success never bypasses these boundaries."""

from importlib import import_module
from typing import Any

import numpy as np
import pytest

from roadmap_tools import exercise_call

starter = import_module("labs.03_real_rag.end_to_end.starter")
rt = import_module("labs.03_real_rag.end_to_end.runtime")


def test_pooling_is_padding_invariant() -> None:
    first = exercise_call(starter.pool_tokens, [[[3.0, 0.0], [0.0, 4.0]]], [[1, 1]])
    padded = exercise_call(
        starter.pool_tokens, [[[3.0, 0.0], [0.0, 4.0], [20.0, -30.0]]], [[1, 1, 0]]
    )
    np.testing.assert_allclose(first, [[0.6, 0.8]])
    np.testing.assert_allclose(padded, first)


@pytest.mark.parametrize("mask", [[[0, 0]], [[1]], [[2, 1]]])
def test_pooling_rejects_invalid_masks(mask: list[list[int]]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.pool_tokens, [[[3.0, 0.0], [0.0, 4.0]]], mask)


def test_actual_dense_result_is_the_provider_context() -> None:
    case = dict(rt.teacher_cases()[0], case_id="independent", query="copy dpi?")
    chunks = rt.teacher_chunks()
    seen: list[Any] = []

    def provider(query: str, passages: tuple[Any, ...]) -> Any:
        seen.extend(passages)
        return rt.demo.Draft("300 dpi", (passages[0].chunk_id,))

    result = exercise_call(
        starter.answer_case,
        case,
        chunks,
        [[0.9, 0.1], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]],
        [1.0, 0.0],
        rt.Config(k=1),
        provider,
    )
    assert [p.chunk_id for p in seen] == [chunks[0].chunk_id]
    assert result["retrieval"]["recall_at_k"] == 1
    assert result["answer_metrics"]["correct"] is True
    assert result["answer_metrics"]["supported"] is True
    assert result["answer"]["status"] == "answer"


@pytest.mark.parametrize("kind", ["missing", "acl", "stale", "ambiguous"])
def test_policy_handles_missing_stale_acl_and_ambiguous(kind: str) -> None:
    case = next(row for row in rt.teacher_cases() if row["kind"] == kind)

    def forbidden(*args: object) -> None:
        pytest.fail("generator must not receive unsafe/absent/ambiguous context")

    result = exercise_call(
        starter.answer_case,
        case,
        rt.teacher_chunks(),
        [[1.0, 0.0]] * 4,
        [-1.0, 0.0] if kind == "missing" else [1.0, 0.0],
        rt.Config(),
        forbidden,
    )
    assert result["answer"]["status"] == "no_answer"
    assert result["answer_metrics"]["abstention_correct"] is True


def test_gold_labels_cannot_change_the_generated_answer() -> None:
    case = rt.teacher_cases()[0]
    vectors = [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]]

    def wrong(query: str, passages: tuple[Any, ...]) -> Any:
        return rt.demo.Draft("900 dpi", (passages[0].chunk_id,))

    def run(row: dict[str, Any]) -> Any:
        return exercise_call(
            starter.answer_case,
            row,
            rt.teacher_chunks(),
            vectors,
            [1.0, 0.0],
            rt.Config(k=1),
            wrong,
        )

    result = run(case)
    changed = run(
        dict(
            case, kind="missing", relevant_ids=[], expected_answers=["900 dpi"], should_abstain=True
        )
    )
    assert result["answer"] == changed["answer"]
    assert result["retrieval"]["recall_at_k"] == 1
    assert result["answer_metrics"]["correct"] is False
    assert result["answer_metrics"]["supported"] is False
