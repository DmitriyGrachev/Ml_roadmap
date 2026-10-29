"""Learner contracts; untouched boundaries cannot pass strict completion."""

from copy import deepcopy
from importlib import import_module
from typing import Any

import pytest

from roadmap_tools.exercise import exercise_call

starter = import_module("labs.04_llm_finetuning.sft_workflow.starter")


def rows() -> list[dict[str, Any]]:
    return [
        {
            "id": str(i),
            "family": f"f{i}",
            "supported": True,
            "expected": {"tag": str(i)},
            "messages": [
                {"role": "user", "content": f"tag {i}"},
                {"role": "assistant", "content": '{"tag":"' + str(i) + '"}'},
            ],
        }
        for i in range(3)
    ]


def test_valid_schema_and_family_isolation() -> None:
    data = rows()
    data.append(dict(deepcopy(data[0]), id="paraphrase"))
    exercise_call(starter.validate_conversations, data)
    split = exercise_call(
        starter.split_conversations, data, {"f0": "train", "f1": "validation", "f2": "holdout"}
    )
    assert set(split) == {"train", "validation", "holdout"}
    assert {row["id"] for row in split["train"]} == {"0", "paraphrase"}
    assert [row["id"] for row in split["holdout"]] == ["2"]


@pytest.mark.parametrize("bad", ["duplicate", "role", "empty", "json", "unsupported"])
def test_invalid_schema(bad: str) -> None:
    data = rows()
    if bad == "duplicate":
        data[1]["id"] = data[0]["id"]
    elif bad == "role":
        data[0]["messages"][1]["role"] = "user"
    elif bad == "empty":
        data[0]["family"] = ""
    elif bad == "json":
        data[0]["messages"][1]["content"] = "not JSON"
    else:
        data[0]["supported"] = False
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.validate_conversations, data)


@pytest.mark.parametrize(
    "assignments",
    [
        {"f0": "train"},
        {"f0": "train", "f1": "train", "f2": "train"},
        {"f0": "train", "f1": "validation", "f2": "test"},
    ],
)
def test_invalid_splits(assignments: dict[str, str]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.split_conversations, rows(), assignments)


class TemplateProbe:
    """Contract spy only: real tokenizer coverage is in explicit library smoke."""

    pad_token_id = 0

    def __init__(self, mask: bool = True) -> None:
        self.calls = 0
        self.mask = mask

    def apply_chat_template(self, messages: Any, **kwargs: Any) -> dict[str, list[int]]:
        self.calls += 1
        assert messages == rows()[0]["messages"]
        assert kwargs.get("tokenize") is True
        assert kwargs.get("return_dict") is True
        assert kwargs.get("return_assistant_tokens_mask") is True
        result = {"input_ids": [1, 2, 3, 4, 5], "attention_mask": [1] * 5}
        if self.mask:
            result["assistant_masks"] = [0, 0, 0, 1, 1]
        return result


def test_template_called_and_targets_not_shifted() -> None:
    tokenizer = TemplateProbe()
    result = exercise_call(starter.encode_conversation, tokenizer, rows()[0], 7)
    assert tokenizer.calls >= 1
    assert result == {
        "input_ids": [1, 2, 3, 4, 5, 0, 0],
        "attention_mask": [1, 1, 1, 1, 1, 0, 0],
        "labels": [-100, -100, -100, 4, 5, -100, -100],
    }


@pytest.mark.parametrize(("length", "mask"), [(3, True), (7, False)])
def test_no_silent_answer_truncation_or_missing_mask(length: int, mask: bool) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - learner chooses diagnostic text
        exercise_call(starter.encode_conversation, TemplateProbe(mask), rows()[0], length)
