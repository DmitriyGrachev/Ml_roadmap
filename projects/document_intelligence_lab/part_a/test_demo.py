"""Real local random encoder reload; no pretrained quality assertion."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytest.importorskip("torch", reason="Opt-in training group required for encoder mechanics")
pytest.importorskip("transformers", reason="Opt-in training group required")


def test_local_teacher_reuses_a1_cohort_and_hf_loader(tmp_path: Path) -> None:
    assert Path(__file__).with_name("demo.py").is_file(), "Teacher encoder integration missing"
    demo = importlib.import_module("projects.document_intelligence_lab.part_a.demo")
    report = demo.run_demo(tmp_path / "new")
    assert report["evidence_kind"] == "teacher-random"
    assert report["pretrained_quality"] == "NOT_RUN"
    assert set(report["methods"]) == {"rules", "tfidf-linear", "encoder"}
    assert report["reload_parity"] is True
    assert report["shapes"]["logits"] == [2, 3]
    assert report["shapes"]["input_ids"][0] == 2
    assert report["shapes"]["attention_mask"] == report["shapes"]["input_ids"]
    cohort = report["evaluation_ids"]
    assert len(cohort) == len(set(cohort)) > 0
    for method in report["methods"].values():
        assert method["count"] == len(cohort)
    with pytest.raises(FileExistsError):
        demo.run_demo(tmp_path / "new")
