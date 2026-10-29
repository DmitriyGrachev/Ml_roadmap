from importlib import import_module

import pytest

p = import_module("labs.02_huggingface_models.token_classification.protocol")


def test_spans_are_exact_and_sentence_local() -> None:
    assert p.bio_spans(["B-PER", "I-PER", "O", "B-LOC"]) == {("PER", 0, 2), ("LOC", 3, 4)}
    with pytest.raises(ValueError, match="invalid I"):
        p.bio_spans(["I-PER"])
    with pytest.raises(ValueError, match="invalid I"):
        p.bio_spans(["B-LOC", "I-PER"])


def test_coverage_counts_partial_truncated_and_unsupported_entities() -> None:
    result = p.entity_coverage(
        ["B-PER", "I-PER", "O", "B-LOC", "B-ORG"], [0, 1, 2, 3], {"PER", "LOC"}
    )
    assert result == {
        "entities": 3,
        "supported_complete": 2,
        "truncated_entities": 1,
        "unsupported_entities": 1,
    }
    assert p.entity_coverage(["B-PER", "I-PER"], [0], {"PER"})["truncated_entities"] == 1


def test_annotations_reject_duplicate_ids_and_wrong_lengths() -> None:
    row = {"id": "a", "words": ["Ada"], "tags": ["B-PER"]}
    with pytest.raises(ValueError, match="overlap"):
        p.validate_annotations({"train": [row], "validation": [row], "test": [row]})
    with pytest.raises(ValueError, match="length"):
        p.validate_annotations(
            {
                "train": [dict(row, tags=[])],
                "validation": [dict(row, id="b")],
                "test": [dict(row, id="c")],
            }
        )


def test_fixture_has_independent_heldout_annotation_rows() -> None:
    import json
    from pathlib import Path

    fixture = json.loads(Path(__file__).with_name("fixtures.json").read_text())
    p.validate_annotations(fixture["splits"])
    assert fixture["evidence"] == "ANNOTATION_FIXTURE_ONLY"
    assert p.bio_spans(fixture["splits"]["test"][0]["tags"]) == {("ORG", 3, 5), ("LOC", 7, 9)}


@pytest.mark.parametrize(
    ("words", "tags"),
    [("Ada", ["O", "O", "O"]), (["Ada"], "O")],
)
def test_annotations_require_word_and_tag_lists(
    words: str | list[str], tags: str | list[str]
) -> None:
    splits = {
        split: [{"id": split, "words": ["Ada"], "tags": ["O"]}]
        for split in ("train", "validation", "test")
    }
    p.validate_annotations(splits)
    splits["train"][0].update(words=words, tags=tags)
    with pytest.raises(ValueError, match="lists"):
        p.validate_annotations(splits)
