"""Small Document Intelligence author walkthrough; no random encoder quality claims."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from projects.external_tabular.evidence import json_bytes

from ..contracts import classification_metrics, validate_dataset, validate_splits


def run(output: Path) -> dict[str, Any]:
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty")
    records = []
    for index, text in enumerate(
        (
            "open account",
            "close account",
            "create membership",
            "delete membership",
            "start a profile",
            "remove my profile",
        )
    ):
        records.append(
            {
                "row_id": f"author-{index}",
                "text": text,
                "label": "create" if index % 2 == 0 else "delete",
                "group_id": f"author-group-{index}",
                "source_id": "author-fixture",
                "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        )
    data = {"schema_version": 1, "labels": ["create", "delete"], "records": records}
    dataset = validate_dataset(data)
    splits = {
        "train": ["author-0", "author-1"],
        "validation": ["author-2", "author-3"],
        "test": ["author-4", "author-5"],
    }
    validate_splits(splits, dataset)
    predictions = [
        {"row_id": "author-4", "predicted_label": "create"},
        {"row_id": "author-5", "predicted_label": "create"},
    ]
    metrics = classification_metrics(dataset, splits["test"], predictions)
    output.mkdir(parents=True, exist_ok=True)
    for name, value in {
        "data": data,
        "splits": splits,
        "predictions": {"rows": predictions},
        "metrics": metrics,
        "manifest": {
            "schema_version": 1,
            "project_id": "document-external-model-study",
            "evidence_kind": "AUTHOR_FIXTURE_ONLY",
            "pretrained_quality": "NOT_RUN",
        },
    }.items():
        (output / (name + ".json")).write_bytes(json_bytes(value))
    return {
        "technical_status": "AUTHOR_FIXTURE_ONLY",
        "pretrained_quality": "NOT_RUN",
        "human_review": "REQUIRED",
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline document contract walkthrough only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.output))


if __name__ == "__main__":
    main()
