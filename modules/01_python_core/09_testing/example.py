"""Keep a currency-validation rule small enough for parametrized tests."""


def is_currency_code(value: str) -> bool:
    return len(value) == 3 and value.isalpha() and value.isupper()


def main() -> None:
    for code in ("EUR", "usd", "EURO"):
        print(f"{code}: {is_currency_code(code)}")


if __name__ == "__main__":
    main()
