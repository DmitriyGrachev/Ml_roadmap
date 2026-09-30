"""Small handwritten artifact fixture, not a release builder or learner answer."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence import validate_evidence


def save(path: Path, value: object) -> str:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def artifact(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    inputs, output = tmp_path / "inputs", tmp_path / "release"
    inputs.mkdir()
    output.mkdir()
    (inputs / "source_a.csv").write_text("id,amount\nunit-A,5\n", encoding="utf-8")
    (inputs / "source_b.jsonl").write_text("", encoding="utf-8")
    (inputs / "labels.csv").write_text("id,label\nunit-A,yes\n", encoding="utf-8")
    sources = {
        name: hashlib.sha256((inputs / name).read_bytes()).hexdigest()
        for name in ("source_a.csv", "source_b.jsonl", "labels.csv")
    }
    save(
        inputs / "provenance.json",
        {"origin": "handwritten isolated validator unit", "license": "CC0-1.0", "sources": sources},
    )
    row_id = hashlib.sha256(b"source_a.csv:2").hexdigest()
    split = "test" if int(hashlib.sha256(b"unit-A").hexdigest(), 16) % 10 < 2 else "train"
    row = {
        "row_id": row_id,
        "source": "source_a.csv",
        "line": 2,
        "business_id": "unit-A",
        "amount": 5.0,
        "label": "yes",
        "reason": "accepted",
        "split": split,
    }
    hashes = {"accepted.jsonl": save(output / "accepted.jsonl", row)}
    for name in ("rejected.jsonl", "review.jsonl"):
        (output / name).write_text("", encoding="utf-8")
        hashes[name] = hashlib.sha256(b"").hexdigest()
    hashes["splits.json"] = save(output / "splits.json", {row_id: split})
    hashes["schema.json"] = save(output / "schema.json", {"version": 1, "rubric_version": 1})
    (output / "memory.md").write_text("Manual analysis pending", encoding="utf-8")
    hashes["memory.md"] = hashlib.sha256((output / "memory.md").read_bytes()).hexdigest()
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "exercise_id": "data-release-study",
        "dataset_sha256": hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest(),
        "split_sha256": hashes["splits.json"],
        "config": {"batch_size": 2},
        "complete": True,
        "rubric_version": 1,
        "sources": sources,
        "origin": "handwritten isolated validator unit",
        "license": "CC0-1.0",
        "artifacts": hashes,
        "counts": {"accepted": 1, "rejected": 0, "review": 0},
        "resources": {
            "buffer_limit_pages": 3,
            "peak_buffer_records": 1,
            "index_strategy": "bounded unit example",
            "index_limit": 1,
        },
    }
    save(output / "manifest.json", manifest)
    return inputs, output, manifest


def test_valid_bytes_are_consistent_but_review_is_still_required(
    artifact: tuple[Path, Path, dict[str, Any]],
) -> None:
    inputs, output, _ = artifact
    assert validate_evidence(output, input_dir=inputs) == "REQUIRES_REVIEW"


@pytest.mark.parametrize("output_amount", [True, 1, 1.0], ids=["bool", "int", "float"])
def test_amount_schema_distinguishes_boolean_from_numeric_one(
    artifact: tuple[Path, Path, dict[str, Any]], output_amount: bool | int | float
) -> None:
    inputs, output, manifest = artifact
    source = inputs / "source_a.csv"
    source.write_text("id,amount\nunit-A,1\n", encoding="utf-8")
    manifest["sources"][source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
    provenance = json.loads((inputs / "provenance.json").read_text(encoding="utf-8"))
    provenance["sources"] = manifest["sources"]
    save(inputs / "provenance.json", provenance)
    manifest["dataset_sha256"] = hashlib.sha256(
        json.dumps(manifest["sources"], sort_keys=True).encode()
    ).hexdigest()
    row = json.loads((output / "accepted.jsonl").read_text(encoding="utf-8"))
    row["amount"] = output_amount
    manifest["artifacts"]["accepted.jsonl"] = save(output / "accepted.jsonl", row)
    save(output / "manifest.json", manifest)
    # All bytes and identities agree: rejection must reach the row schema check.
    if type(output_amount) is bool:
        with pytest.raises(ValueError, match="amount schema"):
            validate_evidence(output, input_dir=inputs)
    else:
        assert validate_evidence(output, input_dir=inputs) == "REQUIRES_REVIEW"


@pytest.mark.parametrize(
    "mutation",
    [
        "partial",
        "schema",
        "split",
        "labels",
        "counts",
        "row",
        "coverage",
        "source",
        "buffer",
        "index",
    ],
)
def test_rejects_plausible_but_inconsistent_artifacts(
    artifact: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    inputs, output, manifest = artifact
    if mutation == "partial":
        manifest["complete"] = False
    elif mutation == "schema":
        manifest["artifacts"]["schema.json"] = save(output / "schema.json", {"version": 9})
    elif mutation == "split":
        digest = save(output / "splits.json", {})
        manifest["artifacts"]["splits.json"] = manifest["split_sha256"] = digest
    elif mutation == "labels":
        (inputs / "labels.csv").write_text("id,label\nunit-A,no\n", encoding="utf-8")
    elif mutation == "counts":
        manifest["counts"]["accepted"] = 2
    elif mutation == "row":
        row = json.loads((output / "accepted.jsonl").read_text())
        row["amount"] = 500
        manifest["artifacts"]["accepted.jsonl"] = save(output / "accepted.jsonl", row)
    elif mutation == "coverage":
        (output / "accepted.jsonl").write_text("", encoding="utf-8")
        manifest["artifacts"]["accepted.jsonl"] = hashlib.sha256(b"").hexdigest()
        manifest["counts"]["accepted"] = 0
    elif mutation == "source":
        manifest["sources"]["source_a.csv"] = "0" * 64
    elif mutation == "buffer":
        manifest["resources"]["peak_buffer_records"] = 999
    else:
        manifest["resources"]["index_strategy"] = ""
    save(output / "manifest.json", manifest)
    with pytest.raises(
        ValueError, match=r"incomplete|schema|split|sha256|counts|row|source|resource"
    ):
        validate_evidence(output, input_dir=inputs)


@pytest.mark.parametrize(
    "mutation",
    ["bool_count", "bool_schema", "bool_rubric", "blank_memory", "missing_artifact", "path_escape"],
)
def test_rejects_invalid_types_and_missing_evidence(
    artifact: tuple[Path, Path, dict[str, Any]],
    mutation: str,
) -> None:
    inputs, output, manifest = artifact
    if mutation == "bool_count":
        manifest["counts"]["accepted"] = True
    elif mutation == "bool_schema":
        manifest["artifacts"]["schema.json"] = save(
            output / "schema.json", {"version": True, "rubric_version": 1}
        )
    elif mutation == "bool_rubric":
        manifest["rubric_version"] = True
    elif mutation == "blank_memory":
        (output / "memory.md").write_text("", encoding="utf-8")
        manifest["artifacts"]["memory.md"] = hashlib.sha256(b"").hexdigest()
    elif mutation == "missing_artifact":
        del manifest["artifacts"]["review.jsonl"]
    else:
        manifest["artifacts"]["../outside"] = "0" * 64
    save(output / "manifest.json", manifest)
    with pytest.raises(ValueError, match=r"counts|schema|unsupported|memory|incomplete"):
        validate_evidence(output, input_dir=inputs)


def test_bundled_fixture_provenance_matches_current_bytes() -> None:
    fixtures = Path(__file__).with_name("fixtures")
    provenance = json.loads((fixtures / "provenance.json").read_text(encoding="utf-8"))
    for name, digest in provenance["sources"].items():
        assert hashlib.sha256((fixtures / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("case", ["malformed_csv", "ambiguous", "duplicate"])
def test_handwritten_rejected_and_review_records(
    artifact: tuple[Path, Path, dict[str, Any]],
    case: str,
) -> None:
    inputs, output, manifest = artifact
    row = json.loads((output / "accepted.jsonl").read_text())
    if case == "malformed_csv":
        (inputs / "source_a.csv").write_text('id,amount\n"unterminated\n', encoding="utf-8")
        row.update(business_id=None, amount=None, label=None, reason="invalid", split=None)
        status = "rejected"
    elif case == "ambiguous":
        (inputs / "labels.csv").write_text("id,label\nunit-A,yes\nunit-A,no\n", encoding="utf-8")
        row.update(label=None, reason="label", split=None)
        status = "review"
    else:
        (inputs / "source_b.jsonl").write_text(
            '{"business_id":"unit-A","value":5}\n', encoding="utf-8"
        )
        row.update(reason="duplicate", split=None)
        status = "review"
    sources = {
        name: hashlib.sha256((inputs / name).read_bytes()).hexdigest()
        for name in manifest["sources"]
    }
    manifest["sources"] = sources
    manifest["dataset_sha256"] = hashlib.sha256(
        json.dumps(sources, sort_keys=True).encode()
    ).hexdigest()
    provenance = json.loads((inputs / "provenance.json").read_text())
    provenance["sources"] = sources
    save(inputs / "provenance.json", provenance)
    (output / "accepted.jsonl").write_text("", encoding="utf-8")
    manifest["artifacts"]["accepted.jsonl"] = hashlib.sha256(b"").hexdigest()
    rows = [row]
    if case == "duplicate":
        rows.append(
            {
                **row,
                "source": "source_b.jsonl",
                "line": 1,
                "row_id": hashlib.sha256(b"source_b.jsonl:1").hexdigest(),
            }
        )
    path = output / f"{status}.jsonl"
    path.write_text("".join(json.dumps(item) + "\n" for item in rows), encoding="utf-8")
    manifest["artifacts"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest["counts"] = {"accepted": 0, "rejected": 0, "review": 0}
    manifest["counts"][status] = len(rows)
    manifest["split_sha256"] = manifest["artifacts"]["splits.json"] = save(
        output / "splits.json", {}
    )
    save(output / "manifest.json", manifest)
    assert validate_evidence(output, input_dir=inputs) == "REQUIRES_REVIEW"
