"""Tests for the provider-response combination exercise."""

from collections.abc import Iterator
from dataclasses import FrozenInstanceError

import pytest

from roadmap_tools import exercise_call

from .starter import (
    IndexedProviderResponse,
    ProviderResponse,
    combine_provider_responses,
)


class OneShotResponses:
    """Iterable that makes a second traversal an observable failure."""

    def __init__(self, *responses: ProviderResponse) -> None:
        self._responses = responses
        self.iteration_count = 0

    def __iter__(self) -> Iterator[ProviderResponse]:
        self.iteration_count += 1
        if self.iteration_count > 1:
            raise AssertionError("responses were traversed more than once")
        return iter(self._responses)


def response(reference: str, status: str = "ok") -> ProviderResponse:
    return exercise_call(ProviderResponse, reference=reference, status=status)


@pytest.mark.student_exercise
def test_combine_responses_uses_one_based_indexes_and_preserves_order() -> None:
    first = response("ref-001")
    second = response("ref-002", status="retry")

    assert exercise_call(
        combine_provider_responses,
        ["stripe", "adyen"],
        [first, second],
    ) == [
        exercise_call(
            IndexedProviderResponse,
            index=1,
            provider_name="stripe",
            response=first,
        ),
        exercise_call(
            IndexedProviderResponse,
            index=2,
            provider_name="adyen",
            response=second,
        ),
    ]


@pytest.mark.student_exercise
def test_combine_responses_traverses_a_one_shot_iterable_once() -> None:
    responses = OneShotResponses(response("ref-001"), response("ref-002"))

    combined = exercise_call(
        combine_provider_responses,
        ("stripe", "adyen"),
        responses,
    )

    assert [item.response.reference for item in combined] == ["ref-001", "ref-002"]
    assert responses.iteration_count == 1


@pytest.mark.student_exercise
def test_combine_responses_rejects_too_few_responses() -> None:
    responses = (item for item in [response("ref-001")])

    with pytest.raises(ValueError, match="length"):
        exercise_call(
            combine_provider_responses,
            ["stripe", "adyen"],
            responses,
        )


@pytest.mark.student_exercise
def test_combine_responses_rejects_too_many_responses() -> None:
    responses = (
        item
        for item in [
            response("ref-001"),
            response("ref-002"),
        ]
    )

    with pytest.raises(ValueError, match="length"):
        exercise_call(combine_provider_responses, ["stripe"], responses)


@pytest.mark.student_exercise
def test_combine_responses_returns_empty_list_for_empty_inputs() -> None:
    responses: Iterator[ProviderResponse] = iter(())

    assert exercise_call(combine_provider_responses, [], responses) == []


@pytest.mark.parametrize(
    ("record", "field", "replacement"),
    [
        (response("ref-001"), "status", "failed"),
        (
            exercise_call(
                IndexedProviderResponse,
                index=1,
                provider_name="stripe",
                response=response("ref-001"),
            ),
            "index",
            2,
        ),
    ],
)
def test_provider_response_records_are_frozen(
    record: ProviderResponse | IndexedProviderResponse,
    field: str,
    replacement: object,
) -> None:
    with pytest.raises(FrozenInstanceError):
        exercise_call(setattr, record, field, replacement)
