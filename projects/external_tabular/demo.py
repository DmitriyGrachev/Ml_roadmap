"""Executable author walkthrough on a separate synthetic CSV. No learner credit."""

from __future__ import annotations

import argparse
import csv
import io
import time
from pathlib import Path
from typing import Any

from .evidence import json_bytes, make_evaluation, validate_bundle, write_bundle
from .protocol import FEATURES, prepare_records


def fixture_csv() -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";")
    writer.writerow([*FEATURES, "quality"])
    for index in range(80):
        label = index % 2
        # Deliberately easy author toy, with unique feature groups; never real wine evidence.
        writer.writerow(
            [round(0.1 * column + index / 100, 4) for column in range(10)]
            + [9 + 2 * label + index / 1000, 5 + label]
        )
    return stream.getvalue().encode()


def fit_candidates(data: dict[str, Any], splits: dict[str, list[str]]) -> dict[str, Any]:
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier

    rows = {row["row_id"]: row for row in data["records"]}

    def features(part: str) -> list[list[float]]:
        return [[rows[row_id]["features"][name] for name in FEATURES] for row_id in splits[part]]

    def labels(part: str) -> list[int]:
        return [rows[row_id]["label"] for row_id in splits[part]]

    models: dict[str, Any] = {
        "dummy": DummyClassifier(strategy="most_frequent"),
        "linear": make_pipeline(StandardScaler(), LogisticRegression(C=1.0, random_state=17)),
        "tree": DecisionTreeClassifier(max_depth=2, min_samples_leaf=3, random_state=17),
    }
    results = {}
    for name, model in models.items():
        model.fit(features("train"), labels("train"))
        # Fixed configurations here teach protocol, not a tuned solution to the learner dataset.
        model.predict(features("validation"))
        started = time.perf_counter()
        predictions = [int(value) for value in model.predict(features("test"))]
        results[name] = {"predictions": predictions, "seconds": time.perf_counter() - started}
    return results


def run(output: Path) -> dict[str, Any]:
    raw = fixture_csv()
    data = prepare_records(raw)
    ids = [row["row_id"] for row in data["records"]]
    splits = {"train": ids[:48], "validation": ids[48:64], "test": ids[64:]}
    methods = fit_candidates(data, splits)
    evaluation = make_evaluation(data, splits, methods, "linear", "tree")
    payloads = {
        "raw": ("raw.csv", raw),
        "data": ("data.json", json_bytes(data)),
        "splits": ("splits.json", json_bytes(splits)),
        "evaluation": ("evaluation.json", json_bytes(evaluation)),
        "source": (
            "source.json",
            json_bytes(
                {
                    "provider": "synthetic author fixture",
                    "url": "fixture://wine-mechanics",
                    "license": "CC0-1.0",
                    "retrieved_at": "generated locally",
                    "permission_note": "Author synthetic values, no empirical wine-quality claim.",
                }
            ),
        ),
        "code": ("experiment.py", Path(__file__).read_bytes()),
        "analysis": ("analysis.md", "Авторский fixture; внешнее качество NOT_RUN.\n".encode()),
    }
    write_bundle(
        output,
        project_id="ml-external-tabular",
        evidence_kind="AUTHOR_FIXTURE_ONLY",
        payloads=payloads,
    )
    result = validate_bundle(output, project_id="ml-external-tabular", author_fixture=True)
    return {key: result[key] for key in ("technical_status", "human_review", "authorship")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic author walkthrough only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.output))


if __name__ == "__main__":
    main()
