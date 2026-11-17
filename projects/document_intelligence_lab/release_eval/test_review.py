import json
from contextlib import nullcontext
from pathlib import Path

import pytest

from .review import validate_submission
from .run import encode, main


def test_offline_demo_does_not_complete_the_live_practical(tmp_path: Path) -> None:
    folder = tmp_path / "demo"
    assert main(["--output-dir", str(folder)]) == 0
    with pytest.raises(ValueError, match="live"):
        validate_submission(folder)


def test_one_changed_query_is_required(tmp_path: Path) -> None:
    from .run import DEFAULT_CASES, DEFAULT_FRAGMENTS
    from .service import digest

    folder = tmp_path / "edited"
    assert main(["--output-dir", str(folder)]) == 0
    dataset = json.loads(DEFAULT_CASES.read_bytes())
    for i, row in enumerate(dataset["queries"]):
        row["answer_fragments"] = DEFAULT_FRAGMENTS[row["query_id"]]
        row["query_id"] = f"renamed-{i}"
    raw = encode(dataset)
    (folder / "cases.json").write_bytes(raw)
    report = json.loads((folder / "report.json").read_bytes())
    report.update(mode="local", usage_unit="provider_tokens", api_transport="loopback_http")
    report["data_sha256"] = digest(raw)
    (folder / "report.json").write_bytes(encode(report))
    with pytest.raises(ValueError, match="independent"):
        validate_submission(folder)


def test_review_binds_the_decision_to_a_candidate_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from . import run
    from .service import excerpt

    # Fixture for the review contract; no model weights are used in this test.
    monkeypatch.setattr(run, "local_generator", lambda *_: excerpt)
    monkeypatch.setattr(run, "serve_api", lambda api: nullcontext(api.answer))
    dataset = json.loads(run.DEFAULT_CASES.read_bytes())
    for row in dataset["queries"]:
        row["answer_fragments"] = run.DEFAULT_FRAGMENTS[row["query_id"]]
    dataset["queries"][0]["text"] = "scanner configuration"
    cases = tmp_path / "questions.json"
    cases.write_bytes(encode(dataset))
    folder = tmp_path / "submission"
    result = main(
        [
            "--mode",
            "local",
            "--endpoint",
            "http://127.0.0.1:1234/v1/chat/completions",
            "--model",
            "fixture",
            "--model-revision",
            "test",
            "--candidate",
            "regressed",
            "--cases",
            str(cases),
            "--output-dir",
            str(folder),
        ]
    )
    assert result == 1
    (folder / "cases.json").write_bytes(cases.read_bytes())
    report = json.loads((folder / "report.json").read_bytes())
    case = report["candidate"]["cases"][0]
    review = {
        "case_id": case["case_id"],
        "trace_id": case["trace_id"],
        "release_decision": "hold",
        "diagnosis": "The context budget discarded the passage.",
        "rationale": "The candidate lost a previously correct answer.",
    }
    review_file = folder / "review.json"
    review_file.write_bytes(encode(review))
    validate_submission(folder)
    review_file.write_bytes(encode({**review, "release_decision": "ship"}))
    with pytest.raises(ValueError, match="failed gate"):
        validate_submission(folder)
    review_file.write_bytes(
        encode({**review, "trace_id": report["baseline"]["cases"][0]["trace_id"]})
    )
    with pytest.raises(ValueError, match="candidate case"):
        validate_submission(folder)
