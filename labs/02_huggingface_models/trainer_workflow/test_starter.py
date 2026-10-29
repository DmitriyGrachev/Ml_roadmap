from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from roadmap_tools.exercise import exercise_call

s = import_module("labs.02_huggingface_models.trainer_workflow.starter")


def test_metrics_are_argmax_not_probability_average() -> None:
    np = pytest.importorskip("numpy")
    evaluation = type(
        "Evaluation",
        (),
        {
            "predictions": np.array([[1.0, 8.0], [3.0, -1.0], [2.0, 0.0]]),
            "label_ids": np.array([1, 0, 1]),
        },
    )()
    assert exercise_call(s.compute_metrics, evaluation) == {"accuracy": 2 / 3}


def test_real_dataset_map_dynamic_collator_and_arguments(tmp_path: Path) -> None:
    datasets = pytest.importorskip("datasets", reason="uv sync --group trainer")
    transformers = pytest.importorskip("transformers", reason="uv sync --group trainer")
    pytest.importorskip("accelerate", reason="uv sync --group trainer")
    example = import_module("labs.02_huggingface_models.trainer_workflow.example")
    _, tokenizer = example.local_components(tmp_path / "tokenizer")
    dataset = datasets.Dataset.from_list(
        [
            {"id": "a", "text": "red", "label": 0, "audit": "x"},
            {"id": "b", "text": "blue square", "label": 1, "audit": "y"},
        ]
    )
    encoded = exercise_call(s.tokenize_dataset, dataset, tokenizer, 12)
    assert set(encoded.column_names) == {"input_ids", "attention_mask", "token_type_ids", "labels"}
    assert len(encoded[0]["input_ids"]) != len(encoded[1]["input_ids"])
    collator = exercise_call(s.build_collator, tokenizer)
    assert isinstance(collator, transformers.DataCollatorWithPadding)
    batch = collator([encoded[0], encoded[1]])
    assert batch["input_ids"].shape == (2, 4)
    assert batch["attention_mask"][0].tolist() == [1, 1, 1, 0]
    args = exercise_call(s.make_training_arguments, tmp_path / "run", s.RunConfig())
    assert isinstance(args, transformers.TrainingArguments)
    assert args.use_cpu
    assert args.load_best_model_at_end
    assert args.eval_strategy.value == args.save_strategy.value == "steps"
    assert args.eval_steps == args.save_steps == 1
    assert args.metric_for_best_model == "accuracy"
    assert args.greater_is_better
    assert args.save_total_limit == 2
    assert args.max_steps == 2
    assert args.report_to == []


def test_learner_trainer_saves_best_checkpoint_and_reloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("accelerate", reason="uv sync --group trainer")
    example = import_module("labs.02_huggingface_models.trainer_workflow.example")
    model, tokenizer = example.local_components(tmp_path / "tokenizer")
    import torch

    torch.set_num_threads(1)
    rows: dict[str, Any] = {
        name: [
            {"id": name + str(i), "text": text, "label": i % 2}
            for i, text in enumerate(["red", "blue square", "red square"])
        ]
        for name in ("train", "validation", "test")
    }
    transformers = import_module("transformers")
    real_train = transformers.Trainer.train
    trainer_calls: list[Any] = []

    def observed_train(current: Any, *args: Any, **kwargs: Any) -> Any:
        trainer_calls.append(current)
        return real_train(current, *args, **kwargs)

    monkeypatch.setattr(transformers.Trainer, "train", observed_train)
    result = exercise_call(s.train_model, model, tokenizer, rows, tmp_path / "run", s.RunConfig())
    assert trainer_calls, "orchestration must invoke actual Trainer.train"
    assert trainer_calls[0].model is model
    assert trainer_calls[0].state.global_step == 2
    assert result["global_step"] == 2
    assert result["best_metric"] == max(row["eval_accuracy"] for row in result["history"])
    assert len(result["predictions"]) == 3
    assert result["references"] == [0, 1, 0]
    assert result["model_identity"] == result["reload_identity"]
    assert (Path(result["checkpoint_path"]) / "model.safetensors").is_file()
    checkpoint = Path(result["best_checkpoint"])
    model2, _ = example.local_components(tmp_path / "other-tokenizer")
    resumed = exercise_call(
        s.train_model,
        model2,
        tokenizer,
        rows,
        tmp_path / "resumed",
        s.RunConfig(max_steps=3),
        resume_from_checkpoint=checkpoint,
    )
    assert resumed["global_step"] == 3


def test_live_learner_report_is_present() -> None:
    import json

    output = Path(__file__).resolve().parents[3] / "artifacts" / "trainer-learner" / "report.json"
    if not output.is_file():
        pytest.xfail("Explicit local pretrained learner experiment and human review are absent")
    report = json.loads(output.read_text())
    assert report["evidence"] == "LEARNER_LOCAL_PRETRAINED"
    assert report["provenance"]["model_sha256"]
    assert report["provenance"]["dataset_sha256"]
    assert report["model_identity"] == report["reload_identity"]
    protocol = import_module("labs.02_huggingface_models.trainer_workflow.protocol")
    protocol.validate_saved_artifact(
        report["checkpoint_path"],
        "sequence",
        report["model_identity"],
        report["tokenizer_identity"],
    )
    assert report["best_metric"] == max(row["eval_accuracy"] for row in report["history"])
    assert (
        len(report["predictions"]) == len(report["references"]) == len(report["split_ids"]["test"])
    )
    ids = [i for values in report["split_ids"].values() for i in values]
    assert len(ids) == len(set(ids))
    assert report["human_review"].strip()


@pytest.mark.parametrize("kind", ["nonfinite", "wrong_rows", "out_of_range", "empty"])
def test_metrics_rejects_invalid_arrays(kind: str) -> None:
    np = pytest.importorskip("numpy")
    predictions, labels = np.array([[0.0, 1.0], [1.0, 0.0]]), np.array([1, 0])
    if kind == "nonfinite":
        predictions[0, 0] = float("nan")
    elif kind == "wrong_rows":
        labels = labels[:1]
    elif kind == "out_of_range":
        labels[0] = 2
    else:
        predictions, labels = predictions[:0], labels[:0]
    evaluation = type("Evaluation", (), {"predictions": predictions, "label_ids": labels})()
    with pytest.raises(ValueError):  # noqa: PT011 - learner diagnostic text is free
        exercise_call(s.compute_metrics, evaluation)
