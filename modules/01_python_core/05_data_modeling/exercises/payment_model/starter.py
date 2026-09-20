"""Student boundary for an immutable, validated payment value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Payment:
    """A payment with a stable identifier, exact amount, and ISO-like currency."""

    identifier: str
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        """Validate all value-object invariants after field initialization."""
        raise NotImplementedError("validate the frozen payment model")
