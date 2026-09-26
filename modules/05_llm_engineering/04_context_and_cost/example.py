"""Estimate cost from supplied rates, without claiming current provider prices."""

from decimal import Decimal


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    input_rate_per_million: Decimal,
    output_rate_per_million: Decimal,
) -> Decimal:
    """Estimate one uncached text request; rates are in the caller's currency."""
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be nonnegative")
    for rate in (input_rate_per_million, output_rate_per_million):
        if not rate.is_finite() or rate < 0:
            raise ValueError("rates must be finite and nonnegative")
    return (
        Decimal(input_tokens) * input_rate_per_million
        + Decimal(output_tokens) * output_rate_per_million
    ) / Decimal(1_000_000)


def main() -> None:
    estimate = estimate_cost(1200, 300, Decimal("2"), Decimal("8"))
    print(f"Illustrative supplied rates: estimated cost = {estimate}")
    print("30 character-budget units are not a claim of 30 model tokens.")
    print("Keep room for output and message framing before selecting source excerpts.")


if __name__ == "__main__":
    main()
