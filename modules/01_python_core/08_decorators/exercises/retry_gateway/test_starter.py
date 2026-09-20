"""Acceptance tests for the parameterized retry decorator."""

import pytest

from roadmap_tools import exercise_call

from .starter import retry


class TransientGatewayError(RuntimeError):
    """A retryable error used by the exercise tests."""


class InvalidGatewayRequest(RuntimeError):
    """A non-retryable error used by the exercise tests."""


@pytest.mark.parametrize("attempts", [0, -1])
def test_retry_rejects_a_non_positive_attempt_count(attempts: int) -> None:
    with pytest.raises(ValueError, match="attempts"):
        exercise_call(retry, attempts=attempts, retry_on=(TransientGatewayError,))


@pytest.mark.student_exercise
def test_retry_returns_after_success_and_uses_the_exact_number_of_calls() -> None:
    calls = 0

    def authorize() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TransientGatewayError("try again")
        return "authorized"

    wrapped = exercise_call(
        retry(attempts=4, retry_on=(TransientGatewayError,)),
        authorize,
    )

    assert exercise_call(wrapped) == "authorized"
    assert calls == 3


@pytest.mark.student_exercise
def test_retry_propagates_the_last_retryable_error_after_exhaustion() -> None:
    errors = [TransientGatewayError("first"), TransientGatewayError("last")]
    calls = 0

    def authorize() -> None:
        nonlocal calls
        error = errors[calls]
        calls += 1
        raise error

    wrapped = exercise_call(
        retry(attempts=2, retry_on=(TransientGatewayError,)),
        authorize,
    )

    with pytest.raises(TransientGatewayError) as caught:
        exercise_call(wrapped)

    assert caught.value is errors[-1]
    assert calls == 2


@pytest.mark.student_exercise
def test_retry_propagates_a_non_retryable_error_immediately() -> None:
    error = InvalidGatewayRequest("invalid payment")
    calls = 0

    def authorize() -> None:
        nonlocal calls
        calls += 1
        raise error

    wrapped = exercise_call(
        retry(attempts=5, retry_on=(TransientGatewayError,)),
        authorize,
    )

    with pytest.raises(InvalidGatewayRequest) as caught:
        exercise_call(wrapped)

    assert caught.value is error
    assert calls == 1


def test_retry_preserves_wrapped_function_metadata() -> None:
    def authorize_payment() -> str:
        """Authorize one payment."""
        return "authorized"

    wrapped = retry(attempts=2, retry_on=(TransientGatewayError,))(authorize_payment)

    assert wrapped.__name__ == "authorize_payment"
    assert wrapped.__doc__ == "Authorize one payment."
