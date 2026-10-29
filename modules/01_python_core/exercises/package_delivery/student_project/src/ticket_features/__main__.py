"""Ready-made CLI; it runs only after the learner implements the adapters."""

import json

from .serve import serving_vector
from .train import training_matrix


def main() -> None:
    records = [
        {"duration_minutes": 30, "priority": " UrGeNt "},
        {"duration_minutes": 240, "priority": "low"},
    ]
    print(json.dumps({"train": training_matrix(records), "serve": serving_vector(records[0])}))


if __name__ == "__main__":
    main()
