"""Training-only dummy baselines for two different prediction contracts."""

import numpy as np
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, recall_score


def baseline_scores() -> dict[str, float]:
    train_x = np.arange(8, dtype=float).reshape(-1, 1)
    test_x = np.arange(8, 12, dtype=float).reshape(-1, 1)
    visits = DummyRegressor(strategy="median").fit(train_x, [10, 12, 14, 16, 18, 20, 22, 24])
    watering = DummyClassifier(strategy="most_frequent").fit(train_x, [0, 0, 0, 0, 0, 0, 1, 1])
    labels = [0, 0, 0, 1]
    predicted = watering.predict(test_x)
    return {
        "visits_mae": float(mean_absolute_error([15, 17, 19, 21], visits.predict(test_x))),
        "watering_accuracy": float(accuracy_score(labels, predicted)),
        "watering_recall": float(recall_score(labels, predicted, zero_division=0)),
    }


def main() -> None:
    print(baseline_scores())


if __name__ == "__main__":
    main()
