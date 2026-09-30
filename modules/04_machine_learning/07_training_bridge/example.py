"""Scalar calibration example, separate from the student's vector update."""


def loss(offset: float) -> float:
    """Squared error for a single synthetic thermometer calibration."""
    return (2.0 * offset - 3.0) ** 2


def gradient(offset: float) -> float:
    """Chain rule: derivative of the outer square times the inner slope."""
    return 4.0 * (2.0 * offset - 3.0)


def step(offset: float, rate: float) -> float:
    """One scalar descent step for this fixed demonstration only."""
    return offset - rate * gradient(offset)


if __name__ == "__main__":
    value = 0.7
    for _ in range(5):
        print(f"offset={value:.5f}, loss={loss(value):.5f}, gradient={gradient(value):.5f}")
        value = step(value, 0.05)
