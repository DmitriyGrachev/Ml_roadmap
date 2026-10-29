"""A fixed train/holdout transform, independent of learner CV or importance."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def run_example() -> dict[str, object]:
    """Fit eight synthetic rows; unseen region and missing score are safe at predict."""
    train = pd.DataFrame(
        {
            "score": [-4.0, -3.0, -2.0, -1.0, 1.0, 2.0, 3.0, 4.0],
            "region": ["east", "west"] * 4,
        }
    )
    holdout = pd.DataFrame({"score": [-5.0, 5.0], "region": ["north", np.nan]})
    preprocess = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
                ),
                ["score"],
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                ["region"],
            ),
        ]
    )
    model = Pipeline(
        [("preprocess", preprocess), ("model", LogisticRegression(C=1.0, random_state=17))]
    )
    model.fit(train, [0, 0, 0, 0, 1, 1, 1, 1])
    fitted = model.named_steps["preprocess"]
    return {
        "train_rows": len(train),
        "heldout_rows": len(holdout),
        "training_median": float(fitted.named_transformers_["num"]["imputer"].statistics_[0]),
        "categories": fitted.named_transformers_["cat"]["encoder"].categories_[0].tolist(),
        "predictions": model.predict(holdout).tolist(),
    }


if __name__ == "__main__":
    print(run_example())
