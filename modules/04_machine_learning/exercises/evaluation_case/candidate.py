"""Supplied candidate to investigate."""

import argparse
import json
from pathlib import Path

from sklearn.tree import DecisionTreeClassifier

from .evidence import summarize
from .fixture import candidate_split, dataset_bytes


def run_candidate(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=False)
    data = dataset_bytes()
    rows = {row["id"]: row for row in json.loads(data)}
    split = candidate_split()
    fields = ["channel", "message_length", "service_code", "touches"]
    train = [rows[key] for key in split["train_ids"]]
    test = [rows[key] for key in split["test_ids"]]
    model = DecisionTreeClassifier(max_depth=3, random_state=7)
    model.fit([[row[field] for field in fields] for row in train], [row["label"] for row in train])
    predictions = [
        int(x) for x in model.predict([[row[field] for field in fields] for row in test])
    ]
    (output_dir / "data.json").write_bytes(data)
    for name, value in {
        "split.json": split,
        "predictions.json": [
            {"id": row["id"], "prediction": prediction}
            for row, prediction in zip(test, predictions, strict=True)
        ],
        "metrics.json": summarize([row["label"] for row in test], predictions),
    }.items():
        (output_dir / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return output_dir / "metrics.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run supplied candidate into a new directory")
    parser.add_argument("output_dir", type=Path)
    print(run_candidate(parser.parse_args().output_dir))
