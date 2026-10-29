"""Offline tests cover gates, not pretrained model quality."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


def api() -> Any:
    try:
        return importlib.import_module(
            "projects.document_intelligence_lab.external_model_study.protocol"
        )
    except ModuleNotFoundError:
        pytest.fail("external pretrained study validator is not implemented")


def test_random_model_cannot_be_relabelled_pretrained() -> None:
    with pytest.raises(ValueError, match=r"pretrained|model|revision"):
        api().validate_pretrained_identity(
            {"id": "local-random-bert", "revision": "fixture-v1", "license": "CC0"}
        )


def test_pretrained_identity_is_pinned_to_existing_lab_manifest() -> None:
    lab = importlib.import_module("labs.02_huggingface_models.download")
    identity = lab.resource_manifest()["model"]
    api().validate_pretrained_identity(identity)
    with pytest.raises(ValueError, match=r"pretrained|model|revision"):
        api().validate_pretrained_identity({**identity, "revision": "main"})


def test_fixture_walkthrough_cannot_satisfy_external_submission(tmp_path: Path) -> None:
    try:
        demo = importlib.import_module(
            "projects.document_intelligence_lab.external_model_study.demo"
        )
    except ModuleNotFoundError:
        pytest.fail("document study walkthrough is not implemented")
    demo.run(tmp_path / "fixture")
    with pytest.raises(ValueError, match=r"external|author|evidence_kind"):
        api().validate_submission(tmp_path / "fixture")


def test_assembler_refuses_random_encoder_reports_before_opening_cache(tmp_path: Path) -> None:
    import json

    try:
        assemble = importlib.import_module(
            "projects.document_intelligence_lab.external_model_study.assemble"
        )
    except ModuleNotFoundError:
        pytest.fail("real-run packaging adapter is not implemented")
    report = tmp_path / "random"
    report.mkdir()
    (report / "report.json").write_text(
        json.dumps({"evidence": "LOCAL_RANDOM_ENCODER_STUDENT_RUN"})
    )
    with pytest.raises(ValueError, match=r"real|pretrained|evidence"):
        assemble.assemble(
            report,
            tmp_path / "cache",
            tmp_path / "output",
            study=tmp_path / "study",
            analysis=tmp_path / "analysis",
            code=tmp_path / "code",
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("change", ["label", "text", "id", "duplicate", "group"])
def test_source_derivation_and_existing_document_split_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    import hashlib

    from projects.external_tabular.evidence import sha256

    lab = importlib.import_module("labs.02_huggingface_models.download")
    raw = tmp_path / "raw.csv"
    raw.write_text(
        "instruction,intent,category\nopen account,create_account,ACCOUNT\n"
        "close account,delete_account,ACCOUNT\nedit account,edit_account,ACCOUNT\n"
        "switch account,switch_account,ACCOUNT\nnew profile,create_account,ACCOUNT\n"
        "remove profile,delete_account,ACCOUNT\n",
        encoding="utf-8",
    )
    # Test-only expected source digest, never a route to bypass public submission validation.
    monkeypatch.setattr(
        lab,
        "resource_manifest",
        lambda: {"dataset": {"id": "test-owned", "files": [{"sha256": sha256(raw)}]}},
    )
    texts = [
        "open account",
        "close account",
        "edit account",
        "switch account",
        "new profile",
        "remove profile",
    ]
    records = [
        {
            "row_id": hashlib.sha256(text.encode()).hexdigest(),
            "text": text,
            "label": [0, 1, 2, 3, 0, 1][i],
            "group_id": f"group-{i}",
        }
        for i, text in enumerate(texts)
    ]
    data = {"classes": [0, 1, 2, 3], "records": records}
    ids = [row["row_id"] for row in records]
    splits = {"train": ids[:4], "validation": [ids[4]], "test": [ids[5]]}
    api().validate_source_records(data, raw, splits)
    if change == "label":
        records[0]["label"] = 1
    elif change == "text":
        records[0]["text"] = "OPEN ACCOUNT"
    elif change == "id":
        records[0]["row_id"] = "invented"
    elif change == "duplicate":
        splits["test"] = [ids[0]]
    else:
        records[-1]["group_id"] = records[0]["group_id"]
    with pytest.raises(ValueError, match=r".+"):
        api().validate_source_records(data, raw, splits)


def test_pretrained_author_smoke_requires_verified_cache_without_downloading(
    tmp_path: Path,
) -> None:
    try:
        module = importlib.import_module(
            "projects.document_intelligence_lab.external_model_study.pretrained_smoke"
        )
    except ModuleNotFoundError:
        pytest.fail("explicit pretrained author smoke is not implemented")
    with pytest.raises(ValueError, match="missing"):
        module.run(tmp_path / "missing-cache", tmp_path / "output")
    assert not (tmp_path / "output").exists()
