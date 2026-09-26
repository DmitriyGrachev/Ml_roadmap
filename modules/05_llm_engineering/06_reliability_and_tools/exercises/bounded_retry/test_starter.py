"""Verify retry timing and failure classification without network or real sleeps."""

from collections.abc import Callable

import pytest

from roadmap_tools import exercise_call

from .starter import PermanentError, Request, TransientError, invoke_with_retry


class ScriptedProvider:
    def __init__(self, outcomes: tuple[str | Exception, ...]) -> None:
        self.outcomes = outcomes
        self.requests: list[Request] = []

    def complete(self, request: Request) -> str:
        self.requests.append(request)
        outcome = self.outcomes[len(self.requests) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_retries_only_after_transient_failures_and_preserves_request_identity() -> None:
    provider = ScriptedProvider((TransientError("busy"), TransientError("timeout"), "Label"))
    request = Request("Describe the telescope", "label-17")
    sleeps: list[float] = []
    result = exercise_call(invoke_with_retry, provider, request, 3, (0.1, 0.4), sleeps.append)
    assert result == "Label"
    assert len(provider.requests) == 3
    assert all(item is request for item in provider.requests)
    assert sleeps == [0.1, 0.4]


def test_success_returns_verbatim_without_sleep_or_extra_attempt() -> None:
    provider = ScriptedProvider(("  Label\n", "wrong"))
    sleeps: list[float] = []
    result = exercise_call(
        invoke_with_retry, provider, Request("Describe", "key"), 2, (1.0,), sleeps.append
    )
    assert result == "  Label\n"
    assert len(provider.requests) == 1
    assert sleeps == []


def test_exhaustion_reraises_final_transient_error_without_final_sleep() -> None:
    final = TransientError("still busy")
    provider = ScriptedProvider((TransientError("busy"), final, "never"))
    sleeps: list[float] = []
    with pytest.raises(TransientError) as caught:
        exercise_call(
            invoke_with_retry, provider, Request("Describe", "key"), 2, (0.5,), sleeps.append
        )
    assert caught.value is final
    assert len(provider.requests) == 2
    assert sleeps == [0.5]


@pytest.mark.parametrize("error", [PermanentError("bad key"), ValueError("bad schema")])
def test_permanent_and_unclassified_errors_are_never_retried(error: Exception) -> None:
    provider = ScriptedProvider((error, "never"))
    sleeps: list[float] = []
    with pytest.raises(type(error)) as caught:
        exercise_call(
            invoke_with_retry, provider, Request("Describe", "key"), 2, (0.5,), sleeps.append
        )
    assert caught.value is error
    assert len(provider.requests) == 1
    assert sleeps == []


def test_one_attempt_allows_no_delay_and_propagates_failure() -> None:
    provider = ScriptedProvider((TransientError("busy"),))
    sleeps: list[float] = []
    with pytest.raises(TransientError):
        exercise_call(invoke_with_retry, provider, Request("Describe", "key"), 1, (), sleeps.append)
    assert len(provider.requests) == 1
    assert sleeps == []


@pytest.mark.parametrize(
    ("attempts", "delays"),
    [
        (0, ()),
        (-1, ()),
        (2, ()),
        (1, (0.1,)),
        (2, (-0.1,)),
        (2, (float("nan"),)),
        (2, (float("inf"),)),
    ],
)
def test_rejects_invalid_retry_policy_before_any_side_effect(
    attempts: int, delays: tuple[float, ...]
) -> None:
    provider = ScriptedProvider(("would succeed",))
    sleeps: list[float] = []
    with pytest.raises(ValueError, match=r"attempt|delay"):
        exercise_call(
            invoke_with_retry, provider, Request("Describe", "key"), attempts, delays, sleeps.append
        )
    assert provider.requests == []
    assert sleeps == []


@pytest.mark.parametrize("query", [Request(" ", "key"), Request("Describe", "\n")])
def test_requires_nonblank_prompt_and_idempotency_key(query: Request) -> None:
    provider = ScriptedProvider(("would succeed",))
    sleeps: list[float] = []
    with pytest.raises(ValueError, match=r"prompt|key"):
        exercise_call(invoke_with_retry, provider, query, 1, (), sleeps.append)
    assert provider.requests == []


def test_sleep_failure_propagates_without_another_provider_call() -> None:
    provider = ScriptedProvider((TransientError("busy"), "never"))

    def interrupted_sleep(delay: float) -> None:
        raise InterruptedError("cancelled")

    sleep: Callable[[float], None] = interrupted_sleep
    with pytest.raises(InterruptedError):
        exercise_call(invoke_with_retry, provider, Request("Describe", "key"), 2, (0.0,), sleep)
    assert len(provider.requests) == 1
