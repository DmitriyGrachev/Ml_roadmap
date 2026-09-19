"""Keep a currency-validation rule small enough for parametrized tests."""

import pytest


def is_currency_code(value: str) -> bool:
    return len(value) == 3 and value.isalpha() and value.isupper()


@pytest.mark.parametrize(
    ("value", "expected"),
    [("EUR", True), ("usd", False), ("EURO", False)],
)
def test_is_currency_code(value: str, expected: bool) -> None:
    assert is_currency_code(value) is expected


def main() -> None:
    print(f"EUR: {is_currency_code('EUR')}")


if __name__ == "__main__":
    main()
