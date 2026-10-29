"""Pure UTF-8 report budget regressions for both independently runnable ranking labs."""

import json
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


@pytest.fixture(params=["neural_reranking", "embedding_adaptation"])
def runtime(request: pytest.FixtureRequest) -> ModuleType:
    return import_module(f"labs.03_real_rag.{request.param}.runtime")


def _data(runtime: ModuleType, text: str) -> dict[str, Any]:
    splits = (
        ["dev", "holdout"]
        if "neural_reranking" in runtime.__name__
        else ["train", "dev", "holdout"]
    )
    queries = [
        {
            "query_id": f"q{i}",
            "query": f"question {i}",
            "family": f"f{i}",
            "split": split,
            "candidate_ids": ["a", "b"],
            "positive_ids": ["a"],
            "hard_negative_ids": ["b"],
        }
        for i, split in enumerate(splits)
    ]
    return {
        "corpus": [{"id": "a", "text": text}, {"id": "b", "text": text}],
        "queries": queries,
        "qrels": {q["query_id"]: {"a": 1} for q in queries},
    }


def _run(
    runtime: ModuleType, data: dict[str, Any], output: Path, provenance: dict[str, Any]
) -> None:
    options = {"steps": 2, "seed": 7} if "embedding_adaptation" in runtime.__name__ else {}
    runtime.run_local(
        output.parent / "unloaded-model", data, output, k=1, provenance=provenance, **options
    )


def test_final_report_boundary_counts_utf8_bytes_without_partial_pass(
    runtime: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = {"status": "PASS", "text": "я字🙂"}
    expected = json.dumps(report, ensure_ascii=False, allow_nan=False).encode("utf-8")
    assert len(expected) > len(expected.decode("utf-8"))
    monkeypatch.setattr(runtime, "MAX_REPORT_BYTES", len(expected))
    runtime._write_report(tmp_path, report)
    assert (tmp_path / "report.json").read_bytes() == expected
    (tmp_path / "report.json").unlink()
    monkeypatch.setattr(runtime, "MAX_REPORT_BYTES", len(expected) - 1)
    with pytest.raises(ValueError, match="report byte budget"):
        runtime._write_report(tmp_path, report)
    assert not (tmp_path / "report.json").exists()


def test_combined_multibyte_input_rejected_before_model_or_output(
    runtime: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runtime, "MAX_REPORT_BYTES", 8000)
    monkeypatch.setattr(runtime, "REPORT_METADATA_RESERVE_BYTES", 0)
    count = 500 if "neural_reranking" in runtime.__name__ else 2000
    validator = (
        runtime.validate_cases if "neural_reranking" in runtime.__name__ else runtime.validate_data
    )
    validator(_data(runtime, "x" * count))

    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("report budget must fail before snapshot/model work")

    monkeypatch.setattr(runtime, "snapshot", forbidden)
    output = tmp_path / "result"
    with pytest.raises(ValueError, match="report byte budget"):
        _run(
            runtime,
            _data(runtime, "🙂" * count),
            output,
            {"kind": "pretrained", "model_id": "local", "revision": "fixed", "license": "reviewed"},
        )
    assert not output.exists()


def test_known_metadata_budget_rejected_before_library_import(
    runtime: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runtime, "MAX_REPORT_BYTES", 8000)
    monkeypatch.setattr(runtime, "REPORT_METADATA_RESERVE_BYTES", 0)
    monkeypatch.setattr(runtime, "snapshot", lambda directory: {"config.json": "0" * 64})

    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("known report budget must fail before optional library import")

    monkeypatch.setattr(runtime, "import_module", forbidden)
    output = tmp_path / "result"
    with pytest.raises(ValueError, match="report byte budget"):
        _run(
            runtime,
            _data(runtime, "small"),
            output,
            {
                "kind": "pretrained",
                "model_id": "🙂" * 3000,
                "revision": "fixed",
                "license": "reviewed",
            },
        )
    assert not output.exists()
