"""Behavioral checks for the offline, teacher-owned RAG walkthrough."""

import importlib
import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

rag = importlib.import_module("modules.06_rag.walkthrough")


def source(source_id: str, text: str, access: str = "public", revision: str = "r1"):
    return rag.Source(source_id, revision, access, text)


def test_tfidf_ranking_uses_actual_weights_and_stable_ties():
    sources = (
        source("a", "apple apple banana"),
        source("b", "banana pear"),
        source("c", "apple apple banana"),
    )
    hits = rag.retrieve("apple", sources, ("public",), k=3)
    assert [hit.chunk_id for hit in hits] == ["a@r1:p1", "c@r1:p1"]
    # Smooth idf(apple)=1+ln(4/3); idf(banana)=1, then L2-normalized TF.
    apple_weight = 2 * (1 + math.log(4 / 3))
    assert hits[0].score == pytest.approx(apple_weight / math.sqrt(apple_weight**2 + 1))
    assert hits[1].score == pytest.approx(hits[0].score)


def test_zero_vocabulary_and_access_filter_leave_no_user_candidates():
    sources = (
        source("public", "Repair appointments."),
        source("protected", "Staff access code DEMO-ONLY.", "staff"),
    )
    assert rag.retrieve("unseen", sources, ("public",), k=2) == ()
    assert rag.retrieve("staff access code", sources, ("public",), k=2) == ()
    assert rag.retrieve("word", (source("punctuation", "... !"),), ("public",), k=2) == ()


def test_access_filter_precedes_top_one_even_when_protected_match_is_stronger():
    sources = (
        source("staff", "overnight storage", "staff"),
        source("guide", "Overnight storage is not offered."),
    )
    hits = rag.retrieve("overnight storage", sources, ("public",), k=1)
    assert [hit.chunk_id for hit in hits] == ["guide@r1:p1"]
    assert hits[0].score > 0


def test_context_rechecks_revision_access_and_budget():
    old = source("guide", "Overnight storage is offered.", revision="old")
    candidate = rag.retrieve("overnight storage", (old,), ("public",), k=1)
    new = source("guide", "Overnight storage is not offered.", revision="new")
    stale = rag.assemble_context(candidate, {"guide": new}, ("public",), 100)
    assert stale.passages == ()
    assert stale.drop_reasons == ("stale_revision",)
    revoked = rag.assemble_context(
        candidate, {"guide": source("guide", old.raw_text, "staff", "old")}, ("public",), 100
    )
    assert revoked.passages == ()
    assert revoked.drop_reasons == ("access_changed",)
    budget = rag.assemble_context(candidate, {"guide": old}, ("public",), 3)
    assert budget.passages == ()
    assert budget.drop_reasons == ("context_budget",)
    tampered = rag.assemble_context(
        (replace(candidate[0], text="Forged indexed snippet."),),
        {"guide": old},
        ("public",),
        100,
    )
    assert tampered.passages == ()
    assert tampered.drop_reasons == ("candidate_mismatch",)


@pytest.mark.parametrize(
    ("case_id", "expected_status", "expected_ids"),
    [
        ("found", "illustrative_answer", ["G-01@2026-09:p1"]),
        ("missed", "abstain_retrieval_miss", []),
        ("absent", "abstain_absent", []),
        ("stale", "abstain_stale", []),
        ("conflict", "abstain_conflict", ["G-01@2026-09:p1", "G-07@2026-09:p1"]),
        ("protected", "abstain_access", []),
    ],
)
def test_author_cases_keep_truth_separate_from_rank(case_id, expected_status, expected_ids):
    trace = rag.build_case(case_id)
    assert trace["answer"]["status"] == expected_status
    assert [passage["chunk_id"] for passage in trace["context"]["passages"]] == expected_ids
    if case_id == "protected":
        assert "G-STAFF" not in json.dumps(trace)
    if case_id == "missed":
        assert trace["teacher_truth"]["relevant_source_ids"] == ["G-01"]
        assert trace["retrieval"]["candidates"] == []
    if case_id == "absent":
        assert trace["teacher_truth"]["relevant_source_ids"] == []


def test_fresh_output_directory_guard_and_offline_cli(tmp_path: Path):
    output = tmp_path / "trace"
    path = rag.save_trace(output)
    assert path == output / "trace.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["policy"]["normalization"] == "unicode-nfc-paragraphs-ws-v1"
    assert saved["cases"]["found"]["retrieval"]["candidates"][0]["score"] > 0
    with pytest.raises(FileExistsError):
        rag.save_trace(output)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileExistsError):
        rag.save_trace(empty)
    cli_output = tmp_path / "cli"
    run = subprocess.run(
        [sys.executable, "-m", "modules.06_rag.walkthrough", "--output", str(cli_output)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert (cli_output / "trace.json").exists()


def test_found_citation_requires_its_passage_in_final_context():
    limited = rag.build_case("found", character_budget=0)
    assert limited["answer"]["status"] == "abstain_context_budget"
    assert limited["answer"]["citation_ids"] == []
    for case_id in rag.CASES:
        trace = rag.build_case(case_id)
        context_ids = {passage["chunk_id"] for passage in trace["context"]["passages"]}
        assert set(trace["answer"]["citation_ids"]) <= context_ids


@pytest.mark.parametrize(
    ("budget", "expected_context"),
    [(60, ["G-01@2026-09:p1"]), (0, [])],
)
def test_conflict_needs_both_current_passages_in_final_context(budget, expected_context):
    trace = rag.build_case("conflict", character_budget=budget)
    assert trace["teacher_truth"]["relevant_source_ids"] == ["G-01", "G-07"]
    assert [passage["chunk_id"] for passage in trace["context"]["passages"]] == expected_context
    assert trace["answer"]["status"] == "abstain_context_budget"
    assert trace["answer"]["citation_ids"] == []


def test_trace_identifies_index_and_current_authorized_snapshots():
    stale = rag.build_case("stale")
    indexed = {item["source_id"]: item for item in stale["retrieval"]["index_snapshot"]}
    current = {item["source_id"]: item for item in stale["context"]["current_snapshot"]}
    assert indexed["G-01"]["revision"] == "2026-08"
    assert current["G-01"]["revision"] == "2026-09"
    assert "G-STAFF" not in json.dumps(stale)
