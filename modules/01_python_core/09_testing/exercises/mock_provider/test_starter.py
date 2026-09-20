"""Acceptance test for one focused provider mock."""

from decimal import Decimal
from typing import cast
from unittest.mock import Mock, call

import pytest

from roadmap_tools import exercise_call

from .starter import QuoteProvider, request_quote


@pytest.mark.student_exercise
def test_request_quote_calls_provider_once_with_original_arguments() -> None:
    provider_mock = Mock(spec=QuoteProvider)
    quote_mock = cast(Mock, provider_mock.quote)
    expected = Decimal("1.234567890123456789")
    quote_mock.return_value = expected

    result = exercise_call(
        request_quote,
        cast(QuoteProvider, provider_mock),
        "merchant-42",
        "EUR",
    )

    assert result == expected
    assert isinstance(result, Decimal)
    assert provider_mock.mock_calls == [call.quote("merchant-42", "EUR")]
