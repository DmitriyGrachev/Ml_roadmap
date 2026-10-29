"""Run the installed package with python -m parcel_features."""

import json

from .serve import serving_vector
from .train import training_matrix


def main() -> None:
    records = [
        {"weight_grams": 2500, "destination": " New   York "},
        {"weight_grams": 0, "destination": "Iași"},
    ]
    print(json.dumps({"train": training_matrix(records), "serve": serving_vector(records[0])}))


if __name__ == "__main__":
    main()
