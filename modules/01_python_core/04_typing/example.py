"""Describe an exchange-rate boundary with a structural protocol."""

from typing import Protocol


class ExchangeRateProvider(Protocol):
    def rate_for(self, currency: str) -> str: ...


class FixedRates:
    def rate_for(self, currency: str) -> str:
        return {"EUR": "1.08", "GBP": "1.27"}.get(currency, "1.00")


def quoted_rate(provider: ExchangeRateProvider, currency: str) -> str:
    return provider.rate_for(currency)


def main() -> None:
    print(quoted_rate(FixedRates(), "EUR"))


if __name__ == "__main__":
    main()
