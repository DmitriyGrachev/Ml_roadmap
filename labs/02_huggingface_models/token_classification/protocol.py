"""Annotation auditing, independent of optional training libraries."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

LABELS = ("O", "B-PER", "I-PER", "B-LOC", "I-LOC", "B-ORG", "I-ORG")


def bio_spans(tags: Sequence[str]) -> set[tuple[str, int, int]]:
    """Strict BIO: an I without preceding B/I of the same type is an error."""
    spans: set[tuple[str, int, int]] = set()
    active: str | None = None
    start = 0
    for index, tag in enumerate([*tags, "O"]):
        if tag != "O" and (len(tag) < 3 or tag[:2] not in ("B-", "I-")):
            raise ValueError("invalid BIO tag")
        if tag.startswith("I-"):
            if active != tag[2:]:
                raise ValueError("invalid I transition")
            continue
        if active is not None:
            spans.add((active, start, index))
            active = None
        if tag.startswith("B-"):
            active, start = tag[2:], index
    return spans


def entity_coverage(
    tags: Sequence[str], complete_word_ids: Sequence[int], supported: set[str]
) -> dict[str, int]:
    """Complete word IDs exclude a word whose last piece was cut by truncation.

    Unsupported and truncated counts can overlap; neither silently enters the
    supported_complete denominator.
    """
    visible = set(complete_word_ids)
    if any(type(i) is not int or i < 0 or i >= len(tags) for i in visible):
        raise ValueError("word id out of range")
    spans = bio_spans(tags)
    return {
        "entities": len(spans),
        "supported_complete": sum(
            t in supported and set(range(a, b)) <= visible for t, a, b in spans
        ),
        "truncated_entities": sum(not set(range(a, b)) <= visible for _, a, b in spans),
        "unsupported_entities": sum(t not in supported for t, _, _ in spans),
    }


def validate_annotations(splits: Mapping[str, Sequence[Mapping[str, Any]]]) -> None:
    if set(splits) != {"train", "validation", "test"} or any(not s for s in splits.values()):
        raise ValueError("nonempty train/validation/test required")
    seen: set[str] = set()
    for rows in splits.values():
        for row in rows:
            if not isinstance(row.get("id"), str) or not row["id"]:
                raise ValueError("invalid id")
            if row["id"] in seen:
                raise ValueError("split overlap or duplicate id")
            seen.add(row["id"])
            words, tags = row.get("words", []), row.get("tags", [])
            if not isinstance(words, list) or not isinstance(tags, list):
                raise ValueError("words and tags must be lists")
            if not words or len(words) != len(tags):
                raise ValueError("word/tag length mismatch")
            if any(not isinstance(w, str) or not w for w in words):
                raise ValueError("invalid word")
            if any(t not in LABELS for t in tags):
                raise ValueError("unsupported label")
            bio_spans(tags)


def validate_report_structure(report: Mapping[str, Any]) -> None:
    splits = report.get("split_ids")
    if not isinstance(splits, dict) or set(splits) != {"train", "validation", "test"}:
        raise ValueError("split_ids must retain all three splits")
    seen: set[str] = set()
    for ids in splits.values():
        if (
            not isinstance(ids, list)
            or not ids
            or any(not isinstance(i, str) or not i for i in ids)
        ):
            raise ValueError("split_ids must contain nonempty ID arrays")
        if seen.intersection(ids) or len(ids) != len(set(ids)):
            raise ValueError("split overlap or duplicate id")
        seen.update(ids)
    if len(report.get("predictions", [])) != len(splits["test"]) or len(
        report.get("references", [])
    ) != len(splits["test"]):
        raise ValueError("test prediction/reference IDs mismatch")
    history = report.get("history")
    if not isinstance(history, list) or not history:
        raise ValueError("history must retain raw validation rows")
    for row in history:
        if not isinstance(row, dict) or not {"step", "eval_loss", "eval_f1"} <= set(row):
            raise ValueError("history requires step, eval_loss and eval_f1")
        for key in ("step", "eval_loss", "eval_f1"):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]):
                raise ValueError("history must contain finite numeric validation values")
        if row["step"] < 0 or row["eval_loss"] < 0 or not 0 <= row["eval_f1"] <= 1:
            raise ValueError("history validation values out of range")
