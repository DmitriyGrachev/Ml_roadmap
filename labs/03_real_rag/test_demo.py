"""Teacher-only contracts; no learner implementation or external runtime."""

import json
from dataclasses import replace
from importlib import import_module
from pathlib import Path

import pytest

demo = import_module("labs.03_real_rag.demo")


def test_acl_is_applied_before_top_k_and_generator() -> None:
    sources = demo.teacher_sources()
    result = demo.answer_query("scanner settings", sources, k=1)
    assert result.status == "answer"
    assert result.citation_ids == ("A-SCAN@1:p1",)
    assert "300 dpi" in result.text
    assert "STAFF-ONLY" not in result.text


def test_missing_evidence_does_not_call_provider() -> None:
    def forbidden(*args: object) -> object:
        pytest.fail("provider must not run with no evidence")

    result = demo.answer_query("volcano insurance", demo.teacher_sources(), generator=forbidden)
    assert result.status == "no_answer"
    assert result.citation_ids == ()


@pytest.mark.parametrize("change", ["deleted", "revision", "acl", "bytes"])
def test_cached_candidates_are_rechecked_before_provider(change: str) -> None:
    sources = demo.teacher_sources()
    target = sources[0]
    if change == "deleted":
        current = sources[1:]
    else:
        replacement = {
            "revision": replace(target, revision="2"),
            "acl": replace(target, access="staff"),
            "bytes": replace(target, raw_text="Scanner settings: 600 dpi."),
        }[change]
        current = (replacement, *sources[1:])
    result = demo.answer_query("scanner settings", sources, current_sources=current, k=1)
    assert result.status == "no_answer"
    assert result.citation_ids == ()


def test_provider_failure_and_recovery_are_separate_outcomes() -> None:
    def unavailable(*args: object) -> object:
        raise demo.ProviderUnavailable("teacher outage")

    failed = demo.answer_query("scanner settings", demo.teacher_sources(), generator=unavailable)
    assert failed.status == "provider_error"
    assert failed.text == ""
    recovered = demo.answer_query("scanner settings", demo.teacher_sources())
    assert recovered.status == "answer"


def test_unavailable_citation_is_not_returned() -> None:
    def invented(*args: object) -> object:
        return demo.Draft("An invented claim", ("A-STAFF@1:p1",))

    result = demo.answer_query("scanner settings", demo.teacher_sources(), generator=invented)
    assert result.status == "invalid_output"
    assert result.text == ""
    assert result.citation_ids == ()


def test_untrusted_document_is_data_and_not_a_tool_instruction() -> None:
    result = demo.answer_query("appendix", demo.teacher_sources(), k=1)
    assert result.status == "answer"
    assert result.text.startswith("Source excerpt: ")
    assert "Ignore previous instructions" in result.text
    assert result.grounding_status == "REQUIRES_REVIEW"


def test_demo_persists_actual_bytes_and_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "teacher"
    result = demo.run_demo(output)
    assert result["retrieval"]["q-exact"]["recall_at_k"] == 1.0
    assert result["retrieval"]["q-paraphrase"]["recall_at_k"] == 0.0
    assert result["pretrained_quality"] == "NOT_RUN"
    demo.verify_trace(output)
    with pytest.raises(FileExistsError):
        demo.run_demo(output)
    (output / "retrieval.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact"):
        demo.verify_trace(output)


@pytest.mark.parametrize("k", [True, 0, -1, 1.5])
def test_rejects_unbounded_or_invalid_query_inputs(k: object) -> None:
    with pytest.raises(ValueError, match="k"):
        demo.answer_query("scanner", demo.teacher_sources(), k=k)


def test_rejects_duplicate_source_identity() -> None:
    sources = demo.teacher_sources()
    with pytest.raises(ValueError, match="unique"):
        demo.answer_query("scanner", (*sources, sources[0]))


@pytest.mark.parametrize("schema", [True, 1.0, "1", None])
def test_trace_rejects_schema_values_with_wrong_type(tmp_path: Path, schema: object) -> None:
    demo.run_demo(tmp_path / "teacher")
    path = tmp_path / "teacher" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = schema
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        demo.verify_trace(path.parent)


@pytest.mark.parametrize("artifacts", [None, [], {"corpus.json": None}])
def test_trace_rejects_malformed_artifact_objects(tmp_path: Path, artifacts: object) -> None:
    demo.run_demo(tmp_path / "teacher")
    path = tmp_path / "teacher" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["artifacts"] = artifacts
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="artifact"):
        demo.verify_trace(path.parent)
