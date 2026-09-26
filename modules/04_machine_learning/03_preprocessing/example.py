"""A numeric pipeline learns state on training measurements only."""

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def training_state() -> dict[str, float]:
    features = np.array([[1.0], [2.0], [np.nan], [4.0], [5.0], [6.0]])
    pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("classify", LogisticRegression(random_state=17)),
        ]
    )
    pipeline.fit(features, [0, 0, 0, 1, 1, 1])
    before = float(pipeline.named_steps["scale"].mean_[0])
    probability = float(pipeline.predict_proba([[100.0]])[0, 1])
    after = float(pipeline.named_steps["scale"].mean_[0])
    return {"training_mean": before, "mean_after_prediction": after, "probability": probability}


def main() -> None:
    print(training_state())


if __name__ == "__main__":
    main()
