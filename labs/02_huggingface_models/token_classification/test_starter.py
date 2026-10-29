from importlib import import_module

import pytest

from roadmap_tools.exercise import exercise_call

s = import_module("labs.02_huggingface_models.token_classification.starter")


def test_first_subword_punctuation_and_all_ignored() -> None:
    assert exercise_call(s.align_labels, [None, 0, 1, 1, 2, 3, None], [1, 0, 3, 0]) == [
        -100,
        1,
        0,
        -100,
        3,
        0,
        -100,
    ]
    assert exercise_call(s.align_labels, [None, None], []) == [-100, -100]
    assert exercise_call(s.align_labels, [None, 0, 0, None], [1, 2]) == [-100, 1, -100, -100]


@pytest.mark.parametrize(
    "ids", [[None, 1], [0, 2], [0, 1, 2], [0, 1, 0], [0, None, 0], [-1], [True]]
)
def test_invalid_alignment(ids: list[int | None]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - learner diagnostic text is free
        exercise_call(s.align_labels, ids, [1, 2])


def test_exact_span_metrics_and_sentence_boundary() -> None:
    actual = exercise_call(
        s.entity_metrics,
        [["B-PER", "O", "B-LOC"], ["B-PER", "I-PER"]],
        [["B-PER", "O", "B-LOC"], ["B-PER", "O"]],
    )
    assert actual == {"precision": 2 / 3, "recall": 2 / 3, "f1": 2 / 3, "tp": 2, "fp": 1, "fn": 1}
    assert exercise_call(s.entity_metrics, [[]], [[]])["f1"] == 0.0
    assert exercise_call(s.entity_metrics, [["O"]], [["B-PER"]])["fn"] == 1


@pytest.mark.parametrize(
    ("pred", "ref"),
    [
        ([["I-PER"]], [["O"]]),
        ([["O"]], [["I-PER"]]),
        ([["O"]], [[]]),
        ([["O"]], []),
        ([["B-PER"], ["I-PER"]], [["B-PER"], ["I-PER"]]),
    ],
)
def test_metrics_reject_invalid_bio_or_lengths(pred: list[list[str]], ref: list[list[str]]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - learner diagnostic text is free
        exercise_call(s.entity_metrics, pred, ref)


def test_learner_uses_real_token_model_and_ignores_padding(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pathlib import Path

    pytest.importorskip("transformers", reason="uv sync --group trainer")
    import torch

    transformers = import_module("transformers")

    torch.set_num_threads(1)
    path = Path(str(tmp_path))
    vocabulary = [
        "[PAD]",
        "[UNK]",
        "[CLS]",
        "[SEP]",
        "[MASK]",
        "ad",
        "##a",
        "visits",
        "rome",
        ".",
        "lee",
    ]
    tokenizer = transformers.BertTokenizerFast(vocab={word: i for i, word in enumerate(vocabulary)})
    labels = {
        i: tag
        for i, tag in enumerate(
            import_module("labs.02_huggingface_models.token_classification.protocol").LABELS
        )
    }
    model = transformers.AutoModelForTokenClassification.from_config(
        transformers.BertConfig(
            vocab_size=len(vocabulary),
            hidden_size=16,
            intermediate_size=24,
            num_hidden_layers=1,
            num_attention_heads=2,
            num_labels=len(labels),
            id2label=labels,
            label2id={v: k for k, v in labels.items()},
        )
    )
    evidence_helper = import_module(
        "labs.02_huggingface_models.token_classification.training_evidence"
    )
    evidence = evidence_helper.observe_optimization(model, monkeypatch)
    rows = {
        split: [
            {
                "id": split + "a",
                "words": ["Ada", "visits", "Rome", "."],
                "tags": ["B-PER", "O", "B-LOC", "O"],
            },
            {"id": split + "b", "words": ["Lee", "."], "tags": ["B-PER", "O"]},
        ]
        for split in ("train", "validation", "test")
    }
    result = exercise_call(s.train_token_classifier, model, tokenizer, rows, path / "run", 1)
    evidence_helper.require_optimization(evidence, model)
    expected = {2: -100, 3: -100, 0: -100, 5: 1, 6: -100, 7: 0, 8: 3, 9: 0, 10: 1}
    for input_ids, labels_batch in zip(evidence.input_ids, evidence.labels, strict=True):
        for token_ids, actual_labels in zip(input_ids.tolist(), labels_batch.tolist(), strict=True):
            assert actual_labels == [expected[token] for token in token_ids]
    assert len(result["predictions"]) == len(result["references"]) == 2
    assert result["span_metrics"] == exercise_call(
        s.entity_metrics, result["predictions"], result["references"]
    )
    assert result["model_identity"] == result["reload_identity"]
    assert (Path(result["checkpoint_path"]) / "model.safetensors").is_file()


def test_live_learner_report_is_present() -> None:
    import json
    from pathlib import Path

    output = Path(__file__).resolve().parents[3] / "artifacts" / "ner-learner" / "report.json"
    if not output.is_file():
        pytest.xfail("Explicit local pretrained learner experiment and human review are absent")
    report = json.loads(output.read_text())
    assert report["evidence"] == "LEARNER_LOCAL_PRETRAINED"
    assert report["provenance"]["model_sha256"]
    assert report["provenance"]["dataset_sha256"]
    assert report["model_identity"] == report["reload_identity"]
    protocol = import_module("labs.02_huggingface_models.token_classification.protocol")
    protocol.validate_report_structure(report)
    artifacts = import_module("labs.02_huggingface_models.trainer_workflow.protocol")
    artifacts.validate_saved_artifact(
        report["checkpoint_path"], "token", report["model_identity"], report["tokenizer_identity"]
    )
    assert report["span_metrics"] == exercise_call(
        s.entity_metrics, report["predictions"], report["references"]
    )
    assert report["human_review"].strip()
    assert set(report["coverage"]) >= {"unsupported_entities", "truncated_entities"}


@pytest.mark.parametrize(
    ("max_length", "expected_steps", "expected_truncated"), [(4, 1, 1), (2, 0, 2)]
)
def test_partial_final_subword_and_all_ignored_training(
    tmp_path: object,
    monkeypatch: pytest.MonkeyPatch,
    max_length: int,
    expected_steps: int,
    expected_truncated: int,
) -> None:
    """Ada is ad/##a: max_length=4 retains only ad; 2 retains no words."""
    from pathlib import Path

    torch = pytest.importorskip("torch", reason="uv sync --group trainer")
    t = pytest.importorskip("transformers", reason="uv sync --group trainer")
    torch.set_num_threads(1)
    vocabulary = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "lee", "ad", "##a"]
    tokenizer = t.BertTokenizerFast(vocab={w: i for i, w in enumerate(vocabulary)})
    labels = dict(
        enumerate(import_module("labs.02_huggingface_models.token_classification.protocol").LABELS)
    )
    model = t.AutoModelForTokenClassification.from_config(
        t.BertConfig(
            vocab_size=len(vocabulary),
            hidden_size=8,
            intermediate_size=12,
            num_hidden_layers=1,
            num_attention_heads=2,
            id2label=labels,
            label2id={v: k for k, v in labels.items()},
        )
    )
    h = import_module("labs.02_huggingface_models.token_classification.training_evidence")
    evidence = h.observe_optimization(model, monkeypatch)
    full = tokenizer(["Lee", "Ada"], is_split_into_words=True)
    cut = tokenizer(
        ["Lee", "Ada"], is_split_into_words=True, truncation=True, max_length=max_length
    )
    assert full.word_ids() == [None, 0, 1, 1, None]
    assert cut.word_ids() == ([None, 0, 1, None] if max_length == 4 else [None, None])
    rows = {
        split: [{"id": split, "words": ["Lee", "Ada"], "tags": ["B-PER", "B-PER"]}]
        for split in ("train", "validation", "test")
    }
    result = exercise_call(
        s.train_token_classifier,
        model,
        tokenizer,
        rows,
        Path(str(tmp_path)) / "run",
        1,
        max_length=max_length,
        batch_size=1,
    )
    assert result["optimizer_steps"] == expected_steps
    assert result["skipped_all_ignored_batches"] == (0 if expected_steps else 1)
    assert result["coverage"] == {
        "entities": 2,
        "supported_complete": 2 - expected_truncated,
        "truncated_entities": expected_truncated,
        "unsupported_entities": 0,
    }
    assert result["references"] == ([["B-PER"]] if expected_steps else [[]])
    if expected_steps:
        h.require_optimization(evidence, model)
        assert evidence.labels
        assert all(batch.tolist() == [[-100, 1, -100, -100]] for batch in evidence.labels)
    else:
        assert not evidence.losses
        assert not evidence.loss_backward
        assert not evidence.gradients
        assert all(
            torch.equal(evidence.before[name], value.detach())
            for name, value in model.named_parameters()
        )


@pytest.mark.parametrize("steps", [True, 0, 101])
def test_learner_budget_rejected_before_training(steps: object, tmp_path: object) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - learner diagnostic text is free
        exercise_call(s.train_token_classifier, None, None, None, tmp_path, steps)
