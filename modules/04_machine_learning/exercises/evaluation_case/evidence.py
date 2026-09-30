"""Read-only evaluation evidence validation."""

import argparse
import json
from pathlib import Path
from typing import Any

from roadmap_tools.open_control_evidence import (
    ids,
    load_bundle,
    object_value,
    read_json,
    require,
    same_numbers,
)

from .fixture import candidate_split, dataset_bytes


def validate_evidence(root: Path) -> None:
    manifest = load_bundle(root, "ml-evaluation-case", {"data.json": dataset_bytes()})
    rows = json.loads(dataset_bytes())
    split = object_value(read_json(root / "split.json"))
    _, test = validate_split(split, [row["id"] for row in rows])
    require(set(test) != set(candidate_split()["test_ids"]), "provide a new evaluation partition")
    outputs = object_value(read_json(root / "outputs.json"))
    validate_outputs(rows, test, outputs, manifest)


def validate_outputs(
    rows: list[dict[str, Any]],
    test: list[str],
    outputs: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    require(outputs.get("run_id") == manifest["run_id"], "prediction run identity differs")
    require(
        outputs.get("dataset_sha256") == manifest["dataset_sha256"], "prediction dataset differs"
    )
    require(outputs.get("split_sha256") == manifest["split_sha256"], "prediction split differs")
    predictions: Any = outputs.get("predictions")
    require(
        isinstance(predictions, list) and all(isinstance(x, dict) for x in predictions),
        "invalid prediction records",
    )
    require([row.get("id") for row in predictions] == test, "prediction IDs differ")
    by_id = {row["id"]: row for row in rows}
    quantities = summarize(
        [by_id[key]["label"] for key in test], [row.get("prediction") for row in predictions]
    )
    same_numbers(quantities, outputs.get("accounting"))


def validate_split(split: dict[str, Any], all_ids: list[str]) -> tuple[list[str], list[str]]:
    train, test = ids(split.get("train_ids")), ids(split.get("test_ids"))
    require(not set(train) & set(test), "split membership overlaps")
    require(set(train + test) == set(all_ids), "split must cover input IDs exactly")
    return train, test


def summarize(labels: list[int], predictions: list[int]) -> dict[str, Any]:
    require(bool(labels) and len(labels) == len(predictions), "prediction count differs")
    require(
        all(type(value) is int and value in (0, 1) for value in labels + predictions),
        "labels and predictions must be binary integers",
    )
    pairs = list(zip(labels, predictions, strict=True))
    correct = sum(left == right for left, right in pairs)
    return {
        "count": len(labels),
        "correct": correct,
        "accuracy": correct / len(labels),
        "tp": pairs.count((1, 1)),
        "tn": pairs.count((0, 0)),
        "fp": pairs.count((0, 1)),
        "fn": pairs.count((1, 0)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate saved bytes without executing source")
    parser.add_argument("root", type=Path)
    validate_evidence(parser.parse_args().root)
    print("Artifact consistency verified; interpretation and provenance REQUIRES_REVIEW")
