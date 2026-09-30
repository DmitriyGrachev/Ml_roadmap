"""Byte identity, replay and explicit local execution consent."""

import json
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

torch = pytest.importorskip("torch", reason="Install the optional training group")
fixtures = import_module("labs.01_pytorch_foundations.debugging.fixtures")
evidence = import_module("labs.01_pytorch_foundations.debugging.evidence")


def make_investigation(tmp_path: Path) -> Path:
    # An independently authored *failing* I/O fixture, never a corrected case.
    source = tmp_path / "instrumentation_input.py"
    source.write_text(
        "import torch\nCONFIG = {'lr': 0.02, 'steps': 8}\n"
        "def step(model, optimizer, x, y, mask):\n"
        "    raise ValueError('fixture observation')\n"
        "def validate(model, x):\n"
        "    model.eval()\n"
        "    with torch.no_grad():\n"
        "        return model(x)\n",
        encoding="utf-8",
    )
    root = tmp_path / "investigation"
    fixtures.run_case("a", root / "before", seed=23)
    fixtures.run_variant("a", source, root / "after", seed=23)
    (root / "report.json").write_text(
        json.dumps(
            {
                "hypotheses": "Infrastructure fixture: deliberately raises an observed exception.",
                "measurements": "One recorded attempted step; no correction claimed.",
                "minimal_change": "Independent failing source, only for validator testing.",
                "defense": "Consistency is not a repaired model or student report.",
                "review_status": "REQUIRES_REVIEW",
            }
        ),
        encoding="utf-8",
    )
    return root


@pytest.fixture
def investigation(tmp_path: Path) -> Path:
    return make_investigation(tmp_path)


def validate(root: Path) -> None:
    evidence.validate_evidence(root, trusted_student_source=root / "after" / "source.py")


def rewrite_run(root: Path, run: dict[str, Any]) -> None:
    torch.save(run, root / "trace.pt")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"]["trace.pt"] = fixtures.digest((root / "trace.pt").read_bytes())
    (root / "manifest.json").write_bytes(fixtures.canonical(manifest))


def test_consistent_observations_are_not_a_claim_of_correction(investigation: Path) -> None:
    validate(investigation)
    with pytest.raises(AssertionError):
        fixtures.assert_healthy(fixtures.load_run(investigation / "after"))


def test_default_never_executes_student_source(investigation: Path) -> None:
    with pytest.raises(ValueError, match="trusted_student_source"):
        evidence.validate_evidence(investigation)


def test_trust_must_name_exact_saved_source(investigation: Path) -> None:
    with pytest.raises(ValueError, match="trusted_student_source"):
        evidence.validate_evidence(
            investigation, trusted_student_source=investigation / "before" / "source.py"
        )


@pytest.mark.parametrize("part", ["before", "after"])
def test_changed_bytes_are_rejected(investigation: Path, part: str) -> None:
    with (investigation / part / "trace.pt").open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="evidence"):
        validate(investigation)


@pytest.mark.parametrize("part", ["before", "after"])
@pytest.mark.parametrize("field", ["before", "ids", "validation", "error"])
def test_rehashed_observations_must_replay(investigation: Path, part: str, field: str) -> None:
    root = investigation / part
    run = fixtures.load_run(root)
    row = run["trace"][0]
    if field == "before":
        row[field] = row[field] + 1
    elif field == "ids":
        row[field] = list(reversed(row[field]))
    elif field == "validation":
        row[field]["outputs"][0] = row[field]["outputs"][0] + 1
    else:
        row[field] = {"type": "ValueError", "message": "invented observation"}
    rewrite_run(root, run)
    with pytest.raises(ValueError, match="replay"):
        validate(investigation)


@pytest.mark.parametrize("field", ["case_id", "seed", "config"])
def test_rejects_incompatible_identity(investigation: Path, field: str) -> None:
    root = investigation / "after"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest[field] = {"case_id": "b", "seed": 99, "config": {"lr": 0.9, "steps": 8}}[field]
    (root / "manifest.json").write_bytes(fixtures.canonical(manifest))
    with pytest.raises(ValueError, match="evidence"):
        validate(investigation)


@pytest.mark.parametrize(
    "field", ["hypotheses", "measurements", "minimal_change", "defense", "review_status"]
)
def test_requires_review_material(investigation: Path, field: str) -> None:
    path = investigation / "report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report.pop(field)
    path.write_bytes(fixtures.canonical(report))
    with pytest.raises(ValueError, match="review"):
        validate(investigation)


def test_does_not_accept_replaced_original_source(investigation: Path) -> None:
    root = investigation / "before"
    (root / "source.py").write_text("raise RuntimeError('must not execute')", encoding="utf-8")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"]["source.py"] = fixtures.digest((root / "source.py").read_bytes())
    (root / "manifest.json").write_bytes(fixtures.canonical(manifest))
    with pytest.raises(ValueError, match="original"):
        validate(investigation)


def test_missing_trust_prevents_execution_even_with_rehashed_source(investigation: Path) -> None:
    root = investigation / "after"
    (root / "source.py").write_text("raise RuntimeError('source executed')", encoding="utf-8")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"]["source.py"] = fixtures.digest((root / "source.py").read_bytes())
    (root / "manifest.json").write_bytes(fixtures.canonical(manifest))
    with pytest.raises(ValueError, match="trusted_student_source"):
        evidence.validate_evidence(investigation)


@pytest.mark.parametrize("name", ["snapshot.json", "split.json"])
def test_rehashed_foreign_data_is_rejected(investigation: Path, name: str) -> None:
    root = investigation / "after"
    (root / name).write_text("[]", encoding="utf-8")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"][name] = fixtures.digest((root / name).read_bytes())
    (root / "manifest.json").write_bytes(fixtures.canonical(manifest))
    with pytest.raises(ValueError, match="evidence"):
        validate(investigation)


def test_matching_changed_identity_still_cannot_compare_different_runs(investigation: Path) -> None:
    root = investigation / "after"
    run = fixtures.load_run(root)
    run["seed"] = 99
    rewrite_run(root, run)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["seed"] = 99
    (root / "manifest.json").write_bytes(fixtures.canonical(manifest))
    with pytest.raises(ValueError, match="same case and seed"):
        validate(investigation)


def test_review_cannot_self_approve(investigation: Path) -> None:
    path = investigation / "report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report["review_status"] = "PASSED"
    path.write_bytes(fixtures.canonical(report))
    with pytest.raises(ValueError, match="review"):
        validate(investigation)
