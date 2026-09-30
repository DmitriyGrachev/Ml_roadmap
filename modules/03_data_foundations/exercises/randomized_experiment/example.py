"""Small synthetic A/A and A/B illustration."""

import numpy as np


def run_example(seed: int = 21) -> dict[str, float | int]:
    """Assign 24 sensors once, then observe each for three fixed time slots."""
    rng = np.random.default_rng(seed)
    arms = np.asarray(["A"] * 12 + ["B"] * 12)
    rng.shuffle(arms)
    baseline = rng.normal(20.0, 1.0, size=24)
    noise = rng.normal(0.0, 0.3, size=(24, 3))
    aa_events = baseline[:, None] + noise
    ab_events = aa_events + (arms == "B")[:, None] * 0.4
    aa_unit_means = aa_events.mean(axis=1)
    ab_unit_means = ab_events.mean(axis=1)
    return {
        "units": 24,
        "events_per_unit": 3,
        "a_units": int(np.sum(arms == "A")),
        "b_units": int(np.sum(arms == "B")),
        "aa_difference": float(
            aa_unit_means[arms == "B"].mean() - aa_unit_means[arms == "A"].mean()
        ),
        "ab_difference": float(
            ab_unit_means[arms == "B"].mean() - ab_unit_means[arms == "A"].mean()
        ),
    }


if __name__ == "__main__":
    print(run_example())
