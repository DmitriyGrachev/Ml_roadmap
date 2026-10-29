"""Data isolation learner checks; completing author smokes never bypasses these."""

from importlib import import_module
from typing import Any

import pytest

from roadmap_tools import exercise_call

s = import_module("labs.03_real_rag.embedding_adaptation.starter")


def rows() -> list[dict[str, Any]]:
    return [
        {
            "query_id": f"q{i}",
            "query": f"question {i}",
            "family": f"f{i}",
            "split": split,
            "positive_ids": ["p", "p"],
            "hard_negative_ids": ["n", "p", "alias", "n"],
        }
        for i, split in enumerate(["train", "dev", "holdout"])
    ]


def test_triples_remove_duplicates_and_false_negatives() -> None:
    corpus = [
        {"id": "p", "text": "Answer"},
        {"id": "alias", "text": " answer "},
        {"id": "n", "text": "Wrong"},
    ]
    triples = exercise_call(s.make_triples, rows()[:1], corpus)
    assert triples == [
        {
            "query_id": "q0",
            "query": "question 0",
            "positive_id": "p",
            "positive": "Answer",
            "negative_id": "n",
            "negative": "Wrong",
            "family": "f0",
            "split": "train",
        }
    ]


def test_unknown_document_is_not_silently_dropped() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        exercise_call(s.make_triples, rows(), [{"id": "p", "text": "Answer"}])


def test_positive_text_aliases_do_not_duplicate_supervision() -> None:
    query = rows()[0]
    query["positive_ids"] = ["p", "alias", "p"]
    corpus = [
        {"id": "p", "text": "Answer"},
        {"id": "alias", "text": " answer "},
        {"id": "n", "text": "Wrong"},
    ]
    triples = exercise_call(s.make_triples, [query], corpus)
    assert len(triples) == 1
    assert triples[0]["positive_id"] == "p"
    assert triples[0]["negative_id"] == "n"


def test_valid_splits_preserve_query_ids() -> None:
    partitions = exercise_call(s.split_queries, rows())
    assert {name: [r["query_id"] for r in group] for name, group in partitions.items()} == {
        "train": ["q0"],
        "dev": ["q1"],
        "holdout": ["q2"],
    }


@pytest.mark.parametrize("field", ["query_id", "query", "family"])
def test_queries_and_document_families_cannot_cross_splits(field: str) -> None:
    queries = rows()
    queries[1][field] = queries[0][field]
    with pytest.raises(ValueError):  # noqa: PT011
        exercise_call(s.split_queries, queries)


def test_normalized_query_duplicate_leaks() -> None:
    queries = rows()
    queries[1]["query"] = "  QUESTION  0 "
    with pytest.raises(ValueError):  # noqa: PT011
        exercise_call(s.split_queries, queries)
