"""A separate sensor lifecycle, not a solution to the support study."""

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


def compare_sensor_ensembles(*, seed: int) -> dict[str, Any]:
    """Small development-only mechanics demo, not a support-study solution."""
    rng = np.random.default_rng(seed)
    features = rng.normal(size=(80, 3))
    labels = (features[:, 0] * features[:, 1] + 0.3 * features[:, 2] > 0).astype(int)
    train, validation = features[:64], features[64:]
    tree = DecisionTreeClassifier(max_depth=3, random_state=seed)
    forest = RandomForestClassifier(
        n_estimators=8,
        max_depth=3,
        max_features="sqrt",
        bootstrap=True,
        random_state=seed,
        n_jobs=1,
    )
    boosting = HistGradientBoostingClassifier(
        max_iter=8,
        max_leaf_nodes=4,
        min_samples_leaf=5,
        learning_rate=0.2,
        early_stopping=False,
        random_state=seed,
    )
    probabilities = {}
    for name, model in (("tree", tree), ("forest", forest), ("boosting", boosting)):
        model.fit(train, labels[:64])
        probabilities[name] = model.predict_proba(validation)[:, 1].tolist()
    tree_probabilities = np.array(
        [member.predict_proba(validation)[:, 1] for member in forest.estimators_]
    )
    stages = list(boosting.staged_predict_proba(validation))
    return {
        "train_count": len(train),
        "validation_count": len(validation),
        "forest_trees": len(forest.estimators_),
        "boosting_stages": len(stages),
        "forest_average_error": float(
            np.max(np.abs(tree_probabilities.mean(axis=0) - probabilities["forest"]))
        ),
        "forest_disagreement": float(tree_probabilities.std(axis=0).mean()),
        "probabilities": probabilities,
        "boosting_validation_brier": [
            float(np.mean((stage[:, 1] - labels[64:]) ** 2)) for stage in stages
        ],
    }


def run_sensor_lifecycle(output_dir: Path, *, seed: int) -> Path:
    """Fit/save/reload our own in-process sensor model in a fresh directory."""
    output_dir.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {"vibration": rng.uniform(0, 10, 40), "temperature": rng.normal(30, 5, 40)}
    )
    labels = (frame["vibration"] > 5).astype(int)
    model = Pipeline(
        [("scale", StandardScaler()), ("classifier", LogisticRegression(random_state=seed))]
    )
    model.fit(frame.iloc[:32], labels.iloc[:32])
    expected = model.predict_proba(frame.iloc[32:])[:, 1]
    data = pickle.dumps(model)
    digest = hashlib.sha256(data).hexdigest()
    path = output_dir / "sensor-model.pkl"
    path.write_bytes(data)
    saved = path.read_bytes()
    if hashlib.sha256(saved).hexdigest() != digest:
        raise ValueError("sensor model bytes changed")
    # Trust comes from creating this object here, not from the checksum.
    restored = pickle.loads(saved)
    actual = restored.predict_proba(frame.iloc[32:])[:, 1]
    np.testing.assert_allclose(expected, actual, rtol=0, atol=0)
    report = output_dir / "sensor-replay.json"
    report.write_text(
        json.dumps(
            {
                "case": "sensor-maintenance",
                "seed": seed,
                "model_sha256": digest,
                "replayed": True,
                "probabilities": actual.tolist(),
            }
        ),
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Separate sensor persistence lifecycle")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    print(json.dumps(compare_sensor_ensembles(seed=args.seed), indent=2))
    print(run_sensor_lifecycle(args.output_dir, seed=args.seed))
