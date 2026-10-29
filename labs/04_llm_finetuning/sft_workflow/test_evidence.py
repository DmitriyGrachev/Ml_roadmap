"""Author consistency tests, not learner completion."""

import json
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

evidence = import_module("labs.04_llm_finetuning.sft_workflow.evidence")


def test_prediction_arithmetic_includes_failed_parse_and_unsupported() -> None:
    rows = [
        {"id": "a", "supported": True, "expected": {"x": 2}},
        {"id": "b", "supported": False, "expected": {"unsupported": True}},
    ]
    assert evidence.score(
        rows, [{"id": "a", "text": "bad"}, {"id": "b", "text": '{"unsupported":true}'}]
    ) == {"parse_success": 0.5, "field_correctness": 0.5, "unsupported_handling": 1.0}
    with pytest.raises(ValueError, match="IDs"):
        evidence.score(rows, [{"id": "a", "text": "{}"}] * 2)


@pytest.mark.parametrize(
    ("origin", "kind"),
    [
        ("AUTHOR", "RANDOM_MECHANISM_ONLY"),
        ("LEARNER", "RANDOM_MECHANISM_ONLY"),
        ("AUTHOR", "LIVE_PRETRAINED"),
    ],
)
def test_teacher_never_satisfies_live_gate(tmp_path: Path, origin: str, kind: str) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "exercise_id": "lab-sft-lora",
                "origin": origin,
                "evidence_kind": kind,
                "review_status": "REQUIRES_REVIEW",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="independent"):
        evidence.validate_evidence(tmp_path)


def test_changed_artifact_and_path_escape(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text("{}", encoding="utf-8")
    digest = evidence.sha256(path)
    assert evidence.checked(tmp_path, "data.json", digest) == path
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        evidence.checked(tmp_path, "data.json", digest)
    with pytest.raises(ValueError, match="inside"):
        evidence.checked(tmp_path, "../outside", digest)


def test_reject_malformed_expected_schema() -> None:
    rows = [
        {"id": "a", "supported": True, "expected": []},
        {"id": "b", "supported": False, "expected": {"unsupported": True}},
    ]
    with pytest.raises(ValueError, match="schema"):
        evidence.score(rows, [{"id": "a", "text": "[]"}, {"id": "b", "text": "{}"}])


@pytest.mark.parametrize("defect", ["family", "heldout_training", "arithmetic", "missing_adapter"])
def test_live_bundle_rejects_leakage_or_forged_metrics(
    tmp_path: Path, defect: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Malformed bundles fail before tensor loading; fake weights never yield a success."""
    original_read = Path.read_text
    observed: dict[str, str] = {}

    def require_utf8(path: Path, *args: Any, **kwargs: Any) -> str:
        assert kwargs.get("encoding") == "utf-8"
        value = original_read(path, *args, **kwargs)
        observed[path.name] = value
        return value

    monkeypatch.setattr(Path, "read_text", require_utf8)
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    for name in ("config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json"):
        (snapshot / name).write_text("{}", encoding="utf-8")
    rows = [
        {
            "id": str(i),
            "family": f"f{i}",
            "supported": i != 3,
            "expected": {"x": i, "label": "маршрут"} if i != 3 else {"unsupported": True},
        }
        for i in range(4)
    ]
    if defect == "family":
        rows[3]["family"] = rows[0]["family"]
    split = {"train": ["0"], "validation": ["1"], "holdout": ["2", "3"]}
    predictions = {
        mode: [
            {"id": row["id"], "text": json.dumps(row["expected"], ensure_ascii=False)}
            for row in rows[2:]
        ]
        for mode in evidence.MODES
    }
    files = {
        "dataset.json": rows,
        "splits.json": split,
        "predictions.json": predictions,
        "adapter/adapter_config.json": {"peft_type": "LORA"},
    }
    for name, value in files.items():
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "runner.py").write_text(
        "# автор: невалидный тестовый fixture, не learner credit\n", encoding="utf-8"
    )
    (tmp_path / "adapter/adapter_model.safetensors").write_text("invalid fixture", encoding="utf-8")
    artifacts = {
        name: evidence.sha256(tmp_path / name)
        for name in (*files, "runner.py", "adapter/adapter_model.safetensors")
    }
    metrics = {mode: evidence.score(rows[2:], predictions[mode]) for mode in evidence.MODES}
    if defect == "arithmetic":
        metrics["lora"]["parse_success"] = 0.0
    identity = {
        "path": str(snapshot),
        "source_revision": "fixture-never-credit",
        "files": {p.name: evidence.sha256(p) for p in snapshot.iterdir()},
    }
    manifest = {
        "exercise_id": "lab-sft-lora",
        "origin": "LEARNER",
        "evidence_kind": "LIVE_PRETRAINED",
        "review_status": "REQUIRES_REVIEW",
        "domain": "test only",
        "authorship_explanation": "test only",
        "base_snapshot": identity,
        "tokenizer_snapshot": identity,
        "artifacts": artifacts,
        "trained_ids": ["0", "3"] if defect == "heldout_training" else ["0"],
        "metrics": metrics,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if defect == "missing_adapter":
        (tmp_path / "adapter/adapter_model.safetensors").unlink()
    with pytest.raises(ValueError, match=r"family|training IDs|arithmetic|artifact"):
        evidence.validate_evidence(tmp_path)
    if defect == "arithmetic":
        assert {
            "manifest.json",
            "runner.py",
            "dataset.json",
            "splits.json",
            "predictions.json",
        } <= observed.keys()
        assert "автор" in observed["runner.py"]
        assert "маршрут" in observed["dataset.json"]
        assert "маршрут" in observed["predictions.json"]


def test_numeric_unsupported_never_gets_boolean_credit() -> None:
    rows = [
        {"id": "a", "supported": True, "expected": {"x": 2}},
        {"id": "b", "supported": False, "expected": {"unsupported": True}},
    ]
    result = evidence.score(
        rows, [{"id": "a", "text": '{"x":2}'}, {"id": "b", "text": '{"unsupported":1}'}]
    )
    assert result["field_correctness"] == 0.5
    assert result["unsupported_handling"] == 0.0
    rows[1]["expected"] = {"unsupported": 1}
    with pytest.raises(ValueError, match="schema"):
        evidence.score(rows, [{"id": "a", "text": "{}"}, {"id": "b", "text": "{}"}])


def test_nested_boolean_number_distinction_and_numeric_normalization() -> None:
    rows = [
        {"id": "a", "supported": True, "expected": {"nested": [{"flag": True}], "n": 1}},
        {"id": "b", "supported": False, "expected": {"unsupported": True}},
    ]
    predicted = [
        {"id": "a", "text": '{"nested":[{"flag":1}],"n":1.0}'},
        {"id": "b", "text": '{"unsupported":true}'},
    ]
    assert evidence.score(rows, predicted)["field_correctness"] == 0.5
    predicted[0]["text"] = '{"nested":[{"flag":true}],"n":1.0}'
    assert evidence.score(rows, predicted)["field_correctness"] == 1.0


@pytest.mark.parametrize(
    "asset",
    [
        "chat_template.jinja",
        "chat_templates/tools.jinja",
        "added_tokens.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "tokenizer.model",
    ],
)
def test_tokenizer_assets_cannot_be_omitted_or_mutated(tmp_path: Path, asset: str) -> None:
    for name in ("tokenizer.json", "tokenizer_config.json", asset):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("проверяемый шаблон", encoding="utf-8")
    identity: dict[str, Any] = {
        "path": str(tmp_path),
        "source_revision": "fixture",
        "files": {
            name: evidence.sha256(tmp_path / name)
            for name in ("tokenizer.json", "tokenizer_config.json")
        },
    }
    with pytest.raises(ValueError, match="tokenizer assets"):
        evidence.validate_snapshot(identity, "tokenizer_snapshot")
    identity["files"][asset] = evidence.sha256(tmp_path / asset)
    evidence.validate_snapshot(identity, "tokenizer_snapshot")
    (tmp_path / asset).write_text("изменённый шаблон", encoding="utf-8")
    with pytest.raises(ValueError, match="changed artifact"):
        evidence.validate_snapshot(identity, "tokenizer_snapshot")
