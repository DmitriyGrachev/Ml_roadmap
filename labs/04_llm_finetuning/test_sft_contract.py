"""The worked token diagram has the same next-token targets as its executable contract."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def targets(ids: list[int], mask: list[int], labels: list[int]) -> list[tuple[int, int]]:
    assert Path(__file__).with_name("sft_contract.py").is_file(), "SFT contract missing"
    module = importlib.import_module("labs.04_llm_finetuning.sft_contract")
    return list(module.causal_targets(ids, mask, labels))


def test_diagram_uses_two_next_token_targets_not_prompt_tokens() -> None:
    assert targets([1, 2, 7, 3, 8, 4], [1] * 6, [-100] * 4 + [8, 4]) == [(3, 8), (4, 4)]


def test_right_padding_does_not_add_a_target() -> None:
    assert targets([1, 3, 8, 4, 0], [1, 1, 1, 1, 0], [-100, -100, 8, 4, -100]) == [
        (1, 8),
        (2, 4),
    ]


@pytest.mark.parametrize(
    ("ids", "mask", "labels"),
    [
        ([1, 2], [1], [-100, 2]),
        ([1, 2], [1, 1], [-100, -100]),
        ([1, 2], [1, 0], [-100, 2]),
        ([1, 2], [True, 1], [-100, 2]),
        ([1, 2], [1, 1], [1, 2]),
        ([1, 2], [1, 1], [-100, 99]),
        ([1, 0, 2], [1, 0, 1], [-100, -100, 2]),
        ([1, -2], [1, 1], [-100, -2]),
    ],
)
def test_bad_or_ambiguous_training_targets_are_rejected(
    ids: list[int],
    mask: list[int],
    labels: list[int],
) -> None:
    with pytest.raises(ValueError, match=r"length|target|padding|integer|mask|token"):
        targets(ids, mask, labels)
