"""A page interval, with independent Decimal and ASCII probes."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PageSpan:
    start: int
    stop: int

    def __post_init__(self) -> None:
        if type(self.start) is not int or type(self.stop) is not int:
            raise ValueError("endpoints must be integers, not bool")
        if self.start < 0 or self.stop < self.start:
            raise ValueError("endpoints require 0 <= start <= stop")

    @property
    def length(self) -> int:
        return self.stop - self.start


def finite_sign(value: Decimal) -> int:
    """Classify a finite measurement; NaN must never reach the comparisons."""
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("value must be a finite Decimal")
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def is_ascii_digits(text: str) -> bool:
    """A separate text probe, not a currency-code validator."""
    return text.isascii() and text.isdecimal()


def main() -> None:
    span = PageSpan(2, 5)
    print(f"span: {span.start}..{span.stop}, length={span.length}")
    print(f"equal values: {span == PageSpan(2, 5)}")
    print(f"empty span length: {PageSpan(5, 5).length}")
    try:
        PageSpan(5, 2)
    except ValueError as error:
        print(f"rejected: {error}")
    print(f"finite sign: {finite_sign(Decimal('-2.5'))}")
    try:
        finite_sign(Decimal("NaN"))
    except ValueError as error:
        print(f"rejected: {error}")
    print(f"ASCII digits: {is_ascii_digits('42')}")
    print(f"Arabic-Indic digits: {is_ascii_digits('٤٢')}")


if __name__ == "__main__":
    main()
