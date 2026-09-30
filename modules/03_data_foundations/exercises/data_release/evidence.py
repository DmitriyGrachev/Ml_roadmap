"""Read-only release consistency checks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact, validate_identity

SOURCE_NAMES = ("source_a.csv", "source_b.jsonl", "labels.csv")
OUTPUT_NAMES = {
    "accepted.jsonl",
    "rejected.jsonl",
    "review.jsonl",
    "splits.json",
    "schema.json",
    "memory.md",
}


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _source_facts(input_dir: Path) -> dict[tuple[str, int], tuple[str | None, float | None]]:
    """Small-fixture audit index; this checker makes no bounded-memory claim."""
    facts = {}
    for name in SOURCE_NAMES[:2]:
        with (input_dir / name).open(encoding="utf-8") as source:
            if name.endswith(".csv") and next(source, "").strip() != "id,amount":
                raise ValueError("source CSV schema")
            for line, raw in enumerate(source, start=2 if name.endswith(".csv") else 1):
                identifier: str | None = None
                amount: float | None = None
                try:
                    if name.endswith(".csv"):
                        fields = next(csv.reader([raw], strict=True))
                        if len(fields) != 2:
                            raise ValueError("source field count")
                        key, value = fields
                    else:
                        record = json.loads(raw)
                        key, value = record["business_id"], record["value"]
                    if isinstance(key, str) and key.strip():
                        identifier = key.strip()
                    if not isinstance(value, bool):
                        number = float(value)
                        if math.isfinite(number) and number > 0:
                            amount = number
                except (ValueError, TypeError, KeyError, StopIteration, csv.Error):
                    pass
                facts[name, line] = identifier, amount
    return facts


def _validate(output_dir: Path, input_dir: Path) -> None:
    manifest = _object(output_dir / "manifest.json")
    provenance = _object(input_dir / "provenance.json")
    sources = provenance["sources"]
    if set(sources) != set(SOURCE_NAMES) or manifest["sources"] != sources:
        raise ValueError("source identity differs")
    for name, digest in sources.items():
        checked_artifact(input_dir, name, digest)
    for field in ("origin", "license"):
        if not isinstance(provenance[field], str) or not provenance[field].strip():
            raise ValueError("missing provenance")
        if manifest[field] != provenance[field]:
            raise ValueError("provenance differs")
    artifacts = manifest["artifacts"]
    if set(artifacts) != OUTPUT_NAMES:
        raise ValueError("incomplete artifacts")
    for name, digest in artifacts.items():
        checked_artifact(output_dir, name, digest)
    validate_identity(
        manifest,
        exercise_id="data-release-study",
        dataset_sha256=hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest(),
        split_sha256=artifacts["splits.json"],
    )
    if (
        manifest["complete"] is not True
        or type(manifest["rubric_version"]) is not int
        or manifest["rubric_version"] != 1
    ):
        raise ValueError("release is incomplete or unsupported")
    schema = _object(output_dir / "schema.json")
    if schema != {"version": 1, "rubric_version": 1} or any(
        type(value) is not int for value in schema.values()
    ):
        raise ValueError("schema differs")
    facts = _source_facts(input_dir)
    frequencies = Counter(identifier for identifier, _ in facts.values() if identifier is not None)
    labels: dict[str, set[str]] = {}
    with (input_dir / "labels.csv").open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["id", "label"]:
            raise ValueError("labels schema")
        for label in reader:
            if label["label"] not in {"yes", "no"} or not label["id"].strip():
                raise ValueError("invalid label row")
            labels.setdefault(label["id"].strip(), set()).add(label["label"])
    seen: set[tuple[str, int]] = set()
    splits: dict[str, str] = {}
    counts = {}
    for status in ("accepted", "rejected", "review"):
        count = 0
        with (output_dir / f"{status}.jsonl").open(encoding="utf-8") as source:
            for raw in source:
                row = json.loads(raw)
                reference = row["source"], row["line"]
                if type(row["line"]) is not int or reference in seen or reference not in facts:
                    raise ValueError("duplicate or unknown source row")
                seen.add(reference)
                identifier, amount = facts[reference]
                if row["amount"] is not None and type(row["amount"]) not in (int, float):
                    raise ValueError("output amount schema requires a JSON number or null")
                row_id = hashlib.sha256(f"{reference[0]}:{reference[1]}".encode()).hexdigest()
                if (
                    row["row_id"] != row_id
                    or row["business_id"] != identifier
                    or row["amount"] != amount
                ):
                    raise ValueError("output row differs from source")
                label_values = labels.get(identifier or "", set())
                if identifier is None or amount is None:
                    expected_status, reason = "rejected", "invalid"
                elif frequencies[identifier] > 1:
                    expected_status, reason = "review", "duplicate"
                elif len(label_values) != 1:
                    expected_status, reason = "review", "label"
                else:
                    expected_status, reason = "accepted", "accepted"
                if status != expected_status or row["reason"] != reason:
                    raise ValueError("rubric decision differs")
                expected_label = next(iter(label_values)) if len(label_values) == 1 else None
                if row["label"] != expected_label:
                    raise ValueError("stale or ambiguous label")
                split = None
                if status == "accepted":
                    split = (
                        "test"
                        if int(hashlib.sha256((identifier or "").encode()).hexdigest(), 16) % 10 < 2
                        else "train"
                    )
                    splits[row_id] = split
                if row["split"] != split:
                    raise ValueError("split differs")
                count += 1
        counts[status] = count
    if (
        seen != set(facts)
        or manifest["counts"] != counts
        or any(type(value) is not int for value in manifest["counts"].values())
    ):
        raise ValueError("row coverage or counts differ")
    if _object(output_dir / "splits.json") != splits:
        raise ValueError("split membership differs")
    batch = manifest["config"]["batch_size"]
    resources = manifest["resources"]
    pages, peak, index_limit = (
        resources[key] for key in ("buffer_limit_pages", "peak_buffer_records", "index_limit")
    )
    if (
        any(type(value) is not int for value in (batch, pages, peak, index_limit))
        or batch <= 0
        or not 1 <= pages <= 8
        or not 0 <= peak <= pages * batch
        or index_limit <= 0
        or not isinstance(resources["index_strategy"], str)
        or not resources["index_strategy"].strip()
    ):
        raise ValueError("invalid declared resource budget")
    if not (output_dir / "memory.md").read_text(encoding="utf-8").strip():
        raise ValueError("missing manual memory report")


def validate_evidence(output_dir: Path, *, input_dir: Path) -> str:
    """Validate existing artifacts against supplied local inputs."""
    try:
        _validate(output_dir, input_dir)
    except (OSError, KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("missing or malformed release evidence") from exc
    return "REQUIRES_REVIEW"


def main() -> None:
    """Inspect saved artifacts only; never manufacture a learner release."""
    parser = argparse.ArgumentParser(description="Check saved release consistency")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--input-dir", type=Path, required=True)
    args = parser.parse_args()
    print(validate_evidence(args.output_dir, input_dir=args.input_dir))


if __name__ == "__main__":
    main()
