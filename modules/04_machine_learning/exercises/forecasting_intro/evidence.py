"""Independent saved one-day forecast readback; no fitted-model provenance claim."""

import argparse
import hashlib
import math
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity
from roadmap_tools.open_control_evidence import ids, object_value, read_json, require, same_numbers

from .fixture import daily_counts, dataset_bytes


def mae(actual: list[float], predictions: list[float]) -> float:
    require(isinstance(predictions, list), "prediction list required")
    require(bool(actual) and len(actual) == len(predictions), "prediction count differs")
    require(
        all(type(x) in (int, float) and math.isfinite(x) for x in actual + predictions),
        "finite numeric predictions required",
    )
    return sum(abs(left - right) for left, right in zip(actual, predictions, strict=True)) / len(
        actual
    )


def validate_outputs(
    split: dict[str, Any], output: dict[str, Any], manifest: dict[str, Any]
) -> None:
    series = daily_counts()
    dates = [str(x.date()) for x in series.index]
    eligible = dates[7:]
    train, test = ids(split.get("train_origins")), ids(split.get("test_origins"))
    require(train + test == eligible and train == sorted(train), "temporal origins differ")
    random_train = ids(split.get("random_train_origins"))
    random_test = ids(split.get("random_test_origins"))
    require(
        not set(random_train) & set(random_test)
        and set(random_train + random_test) == set(eligible),
        "random partition differs",
    )
    for key in ("run_id", "dataset_sha256", "split_sha256"):
        require(output.get(key) == manifest[key], "output identity differs")
    require(
        manifest["config"].get("horizon") == 1 and type(manifest["config"].get("horizon")) is int,
        "only one-day horizon supported",
    )
    require(manifest["config"].get("model_family") == "Ridge", "use existing Ridge family")
    require(output.get("origins") == test, "score origins differ")
    fit = object_value(output.get("fit_origins"))
    require(set(fit) == set(test), "fit origins differ")
    for day in test:
        training = ids(fit[day])
        require(
            set(training) <= set(eligible) and all(x < day for x in training),
            "training target must precede forecast origin",
        )
    predictions = object_value(output.get("predictions"))
    require(set(predictions) == {"naive", "seasonal", "model"}, "three forecast methods required")
    values = dict(zip(dates, series.tolist(), strict=True))
    require(
        predictions["naive"] == [values[dates[dates.index(x) - 1]] for x in test],
        "naive predictions differ",
    )
    require(
        predictions["seasonal"] == [values[dates[dates.index(x) - 7]] for x in test],
        "seasonal predictions differ",
    )
    actual = [values[x] for x in test]
    scores = {name: mae(actual, value) for name, value in predictions.items()}
    same_numbers(scores, output.get("mae"))
    random = object_value(output.get("random"))
    require(random.get("origins") == random_test, "random score origins differ")
    random_score = mae([values[x] for x in random_test], random.get("predictions", []))
    same_numbers(
        {"random_mae": random_score, "temporal_mae": scores["model"]}, output.get("comparison")
    )


def validate_evidence(root: Path) -> None:
    manifest = object_value(read_json(root / "manifest.json"))
    artifacts = object_value(manifest.get("artifacts"))
    require(
        {"data.json", "split.json", "outputs.json", "implementation.txt", "report.md"}
        <= artifacts.keys(),
        "missing artifacts",
    )
    for name, digest in artifacts.items():
        path = checked_artifact(root, name, digest)
        require(bool(path.read_bytes().strip()), "empty artifact")
        if name == "data.json":
            require(path.read_bytes() == dataset_bytes(), "stale dataset")
    validate_identity(
        manifest,
        exercise_id="ml-forecasting-intro",
        dataset_sha256=hashlib.sha256(dataset_bytes()).hexdigest(),
        split_sha256=artifacts["split.json"],
    )
    require(isinstance(manifest.get("run_id"), str) and manifest["run_id"].strip(), "run ID")
    require(manifest.get("review_status") == "REQUIRES_REVIEW", "manual review required")
    validate_outputs(
        object_value(read_json(root / "split.json")),
        object_value(read_json(root / "outputs.json")),
        manifest,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read saved one-day forecast evidence")
    parser.add_argument("root", type=Path)
    validate_evidence(parser.parse_args().root)
    print("Consistency checked; execution and interpretation REQUIRES_REVIEW")
