"""Explicit local fixture generation."""

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def generate(output_dir: Path, *, records: int, seed: int) -> None:
    """Generate finite inputs in a fresh directory."""
    if type(records) is not int or records <= 0:
        raise ValueError("records must be a positive integer")
    output_dir.mkdir(parents=True, exist_ok=False)
    rng = random.Random(seed)
    with (
        (output_dir / "source_a.csv").open("x", encoding="utf-8", newline="") as csv_file,
        (output_dir / "source_b.jsonl").open("x", encoding="utf-8", newline="\n") as json_file,
        (output_dir / "labels.csv").open("x", encoding="utf-8", newline="") as labels_file,
    ):
        writer, labels = csv.writer(csv_file), csv.writer(labels_file)
        writer.writerow(["id", "amount"])
        labels.writerow(["id", "label"])
        for index in range(records):
            identifier = f"item-{index // 2 if index % 7 == 0 else index:06d}"
            amount = str(rng.randint(1, 999)) if index % 11 else "bad"
            if index % 2 == 0:
                writer.writerow([identifier, amount])
            elif index % 13 == 0:
                json_file.write("{malformed\n")
            else:
                json_file.write(json.dumps({"business_id": identifier, "value": amount}) + "\n")
            labels.writerow([identifier, "yes" if index % 3 else "no"])
            if index % 17 == 0:
                labels.writerow([identifier, "yes"])
                labels.writerow([identifier, "no"])
    sources = {}
    for name in ("source_a.csv", "source_b.jsonl", "labels.csv"):
        with (output_dir / name).open("rb") as source:
            sources[name] = hashlib.file_digest(source, "sha256").hexdigest()
    provenance = {
        "origin": "local synthetic teaching fixture",
        "license": "CC0-1.0",
        "records": records,
        "seed": seed,
        "sources": sources,
    }
    with (output_dir / "provenance.json").open("x", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(provenance, sort_keys=True, indent=2) + "\n")


def main() -> None:
    """Never choose a learner output location implicitly."""
    parser = argparse.ArgumentParser(description="Generate local messy inputs explicitly")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--records", type=int, default=200)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()
    generate(args.output_dir, records=args.records, seed=args.seed)


if __name__ == "__main__":
    main()
