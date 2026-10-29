"""Author integrity checks; never give learner credit."""

import hashlib
import json
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

rt = import_module("labs.03_real_rag.embedding_adaptation.runtime")


def data() -> dict[str, Any]:
    return {
        "corpus": [{"id": "a", "text": "Good"}, {"id": "b", "text": "Bad"}],
        "queries": [
            {
                "query_id": f"q{i}",
                "query": f"question {i}",
                "family": f"f{i}",
                "split": split,
                "positive_ids": ["a"],
                "hard_negative_ids": ["b"],
            }
            for i, split in enumerate(["train", "dev", "holdout"])
        ],
    }


def test_valid_data() -> None:
    rt.validate_data(data())


@pytest.mark.parametrize("field", ["query_id", "query", "family", "positive_ids"])
def test_data_rejects_leakage_and_unknown_documents(field: str) -> None:
    rows = data()
    rows["queries"][1][field] = (
        ["unknown"] if field == "positive_ids" else rows["queries"][0][field]
    )
    with pytest.raises(ValueError):  # noqa: PT011
        rt.validate_data(rows)


def test_missing_evidence_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="evidence"):
        rt.validate_submission(tmp_path)


@pytest.fixture
def parser_fixture(tmp_path: Path) -> Path:
    """Fabricated files test read-only integrity only; no model is claimed or loaded."""
    checkpoint = tmp_path / "adapted"
    checkpoint.mkdir()
    (checkpoint / "model.safetensors").write_bytes(b"PARSER FIXTURE, NOT WEIGHTS")
    result = {"q2": {"ids": ["a"], "scores": [0.7], "recall_at_k": 1.0, "mrr_at_k": 1.0}}
    report = {
        "evidence_kind": "LEARNER_LOCAL_PRETRAINED_ADAPTATION",
        "status": "PASS",
        "quality": "REQUIRES_REVIEW",
        "learner_source_sha256": hashlib.sha256(
            Path(str(rt.__file__)).with_name("starter.py").read_bytes()
        ).hexdigest(),
        "data": data(),
        "provenance": {
            "kind": "pretrained",
            "model_id": "PARSER_FIXTURE_ONLY",
            "revision": "NOT_REAL",
            "license": "fixture",
        },
        "baseline_snapshot": {"model.safetensors": "0" * 64},
        "adapted_snapshot": rt.snapshot(checkpoint),
        "baseline_weights_sha256": "0" * 64,
        "adapted_weights_sha256": "1" * 64,
        "reload_weights_equal": True,
        "train_query_ids": ["q0"],
        "objective": "cosine_triplet_margin_0.2",
        "steps": 2,
        "k": 1,
        "baseline": result,
        "adapted": result,
        "dev_baseline": {"q1": result["q2"]},
        "dev_adapted": {"q1": result["q2"]},
        "timing_seconds": {"baseline": 0.1, "adapted": 0.1, "training": 0.1},
    }
    (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "review.json").write_text(
        json.dumps(
            {
                "status": "REQUIRES_REVIEW",
                **{
                    key: "Fabricated parser fixture. Actual provenance needs independent review."
                    for key in (
                        "hypothesis",
                        "dev_selection",
                        "false_negatives",
                        "failures",
                        "transfer",
                        "provenance_review",
                    )
                },
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_consistent_parser_input_does_not_authenticate_weights(parser_fixture: Path) -> None:
    rt.validate_submission(parser_fixture)


@pytest.mark.parametrize(
    "change", ["author", "holdout", "score", "metric", "mrr", "weights", "checkpoint", "train_ids"]
)
def test_submission_tampering_rejected(parser_fixture: Path, change: str) -> None:
    path = parser_fixture / "report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if change == "author":
        report["evidence_kind"] = "AUTHOR_RANDOM_API_SMOKE"
    elif change == "holdout":
        report["adapted"]["other-query"] = report["adapted"].pop("q2")
    elif change == "score":
        report["adapted"]["q2"]["scores"] = []
    elif change == "metric":
        report["adapted"]["q2"]["recall_at_k"] = 0.4
    elif change == "mrr":
        report["adapted"]["q2"]["mrr_at_k"] = 0.4
    elif change == "weights":
        report["adapted_weights_sha256"] = report["baseline_weights_sha256"]
    elif change == "checkpoint":
        (parser_fixture / "adapted" / "model.safetensors").write_bytes(b"changed")
    else:
        report["train_query_ids"] = ["q2"]
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence"):
        rt.validate_submission(parser_fixture)


def test_incomplete_triples_fail_before_output_or_model_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = data()
    rows["queries"].insert(
        1,
        dict(rows["queries"][0], query_id="q-missing", query="uncovered query", family="missing"),
    )
    model_dir = tmp_path / "snapshot"
    model_dir.mkdir()
    (model_dir / "modules.json").write_text("[]", encoding="utf-8")
    output = tmp_path / "output"

    def forbidden_load(*args: object, **kwargs: object) -> None:
        raise AssertionError("model loader reached before triple coverage validation")

    learner = SimpleNamespace(
        split_queries=lambda queries: {
            split: [row for row in queries if row["split"] == split]
            for split in ("train", "dev", "holdout")
        },
        make_triples=lambda queries, corpus: [
            {
                **queries[0],
                "positive_id": "a",
                "negative_id": "b",
                "positive": "Good",
                "negative": "Bad",
            }
        ],
    )
    modules = {
        "sentence_transformers": SimpleNamespace(SentenceTransformer=forbidden_load),
        "torch": SimpleNamespace(set_num_threads=lambda _: None, manual_seed=lambda _: None),
        "labs.03_real_rag.embedding_adaptation.starter": learner,
    }
    monkeypatch.setattr(rt, "import_module", modules.__getitem__)
    with pytest.raises(ValueError, match="cover every train query"):
        rt.run_local(
            model_dir,
            rows,
            output,
            k=1,
            steps=1,
            seed=7,
            provenance={
                "kind": "pretrained",
                "model_id": "fixture",
                "revision": "x",
                "license": "x",
            },
        )
    assert not output.exists()
