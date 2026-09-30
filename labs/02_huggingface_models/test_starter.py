"""Student contracts; xfail means unfinished, never a passing laboratory."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from roadmap_tools.exercise import exercise_call

PACKAGE = "labs.02_huggingface_models"


def assert_comparison_trace(
    observations: Mapping[str, Any],
    results: Mapping[str, Any],
    training: list[Any],
    validation: list[Any],
    testing: list[Any],
) -> None:
    """Check observed orchestration, independently of any accuracy threshold."""
    vectorizer_fits = observations["vectorizer_fits"]
    classifier_fits = observations["classifier_fits"]
    assert vectorizer_fits
    assert all(texts == [row.text for row in training] for texts in vectorizer_fits)
    assert len(classifier_fits) == 2, "both real linear classifiers must be fitted"
    assert all(labels == [row.label for row in training] for _, labels in classifier_fits)
    assert {width for width, _ in classifier_fits} == {observations["tfidf_width"], 16}
    sizes = observations["pooling_batches"]
    assert sizes
    assert sum(sizes) >= len(training) + len(testing)
    assert all(size <= 4 for size in sizes), "respect the configured batch size"
    assert observations["adaptation_calls"] == [
        ([row.row_id for row in training], [row.row_id for row in validation])
    ]
    modes = observations["frozen_forwards"]
    assert modes
    assert all(not train and not grad for train, grad in modes)
    assert observations["frozen_unchanged"] is True
    prediction_events = observations["prediction_events"]
    for index, (width, _) in enumerate(classifier_fits):
        method = "frozen_embeddings" if width == 16 else "tfidf_linear"
        assert prediction_events.get(index), "classifiers must actually predict the test rows"
        assert all(
            predicted == results[method]["predictions"] for predicted in prediction_events[index]
        )


def test_comparison_trace_accepts_complete_evidence_without_quality_threshold() -> None:
    from types import SimpleNamespace

    # Positive *trace* fixture, not an implementation of the learner's model comparison.
    training = [
        SimpleNamespace(row_id="a", text="alpha", label=0),
        SimpleNamespace(row_id="b", text="beta", label=1),
    ]
    validation = [SimpleNamespace(row_id="v", text="validation", label=2)]
    testing = [SimpleNamespace(row_id="t", text="test", label=3)]
    observations = {
        "vectorizer_fits": [["alpha", "beta"]],
        "classifier_fits": [(2, [0, 1]), (16, [0, 1])],
        "tfidf_width": 2,
        "pooling_batches": [2, 1],
        "adaptation_calls": [(["a", "b"], ["v"])],
        "frozen_forwards": [(False, False), (False, False)],
        "frozen_unchanged": True,
        "prediction_events": {0: [[0]], 1: [[1]]},
    }
    # Both predictions are wrong for label 3; computation, not quality, is the contract.
    results = {"tfidf_linear": {"predictions": [0]}, "frozen_embeddings": {"predictions": [1]}}
    assert_comparison_trace(observations, results, training, validation, testing)


def student() -> Any:
    assert Path(__file__).with_name("starter.py").is_file(), "student boundaries are missing"
    return importlib.import_module(f"{PACKAGE}.starter")


@pytest.fixture
def local_model() -> tuple[Any, Any]:
    pytest.importorskip("torch", reason="NOT_RUN: install the opt-in training group")
    pytest.importorskip("transformers", reason="NOT_RUN: install the opt-in training group")
    return cast(
        tuple[Any, Any],
        importlib.import_module(f"{PACKAGE}.example").make_local_components(num_labels=4),
    )


def test_deduplication_before_split_and_stable_source_ids() -> None:
    rows = [
        {"instruction": f"{intent} request {index}", "intent": intent, "category": "ACCOUNT"}
        for intent in ("create_account", "delete_account", "edit_account", "switch_account")
        for index in range(4)
    ]
    rows.append(dict(rows[0]))
    rows.append({"instruction": "unrelated", "intent": "track_order", "category": "ORDER"})
    result = exercise_call(student().prepare_splits, rows, seed=17, counts=(2, 1, 1))
    assert {key: len(value) for key, value in result.items()} == {
        "train": 8,
        "validation": 4,
        "test": 4,
    }
    ids = [record.row_id for values in result.values() for record in values]
    assert len(ids) == len(set(ids)) == 16
    assert result == exercise_call(student().prepare_splits, rows[::-1], seed=17, counts=(2, 1, 1))
    assert all(record.text != "unrelated" for values in result.values() for record in values)


def test_conflicting_duplicate_label_is_rejected() -> None:
    rows = [
        {"instruction": "same text", "intent": intent, "category": "ACCOUNT"}
        for intent in ("create_account", "delete_account")
    ]
    with pytest.raises(ValueError, match="conflict"):
        exercise_call(student().prepare_splits, rows, seed=0, counts=(1, 1, 1))


def test_tokenization_preserves_order_and_limits_length(local_model: tuple[Any, Any]) -> None:
    torch = pytest.importorskip("torch")
    _, tokenizer = local_model
    batch = exercise_call(
        student().encode_batch, tokenizer, ["red", "blue square " * 10], max_length=6
    )
    assert set(batch) == {"input_ids", "attention_mask", "token_type_ids"}
    assert batch["input_ids"].shape == (2, 6)
    assert batch["input_ids"].dtype == torch.long
    assert batch["attention_mask"].tolist() == [[1, 1, 1, 0, 0, 0], [1, 1, 1, 1, 1, 1]]
    assert batch["input_ids"][0, 1] == tokenizer.convert_tokens_to_ids("red")


def test_pooling_ignores_padding_and_normalizes_vectors() -> None:
    torch = pytest.importorskip("torch", reason="NOT_RUN: install the opt-in training group")
    hidden = torch.tensor([[[3.0, 0.0], [0.0, 3.0], [900.0, 900.0]]])
    pooled = exercise_call(student().masked_mean_pool, hidden, torch.tensor([[1, 1, 0]]))
    assert torch.allclose(pooled, torch.tensor([[2**-0.5, 2**-0.5]]), atol=1e-6)
    with pytest.raises(ValueError, match="mask"):
        exercise_call(student().masked_mean_pool, hidden, torch.zeros((1, 3), dtype=torch.long))


def test_empty_text_and_nonfinite_pooling_are_rejected(local_model: tuple[Any, Any]) -> None:
    torch = pytest.importorskip("torch")
    _, tokenizer = local_model
    with pytest.raises(ValueError, match="text"):
        exercise_call(student().encode_batch, tokenizer, [" "], max_length=8)
    with pytest.raises(ValueError, match="finite"):
        exercise_call(
            student().masked_mean_pool, torch.tensor([[[float("nan")]]]), torch.tensor([[1]])
        )


def test_adaptation_updates_only_last_block_and_head(local_model: tuple[Any, Any]) -> None:
    torch = pytest.importorskip("torch")
    model, tokenizer = local_model
    module = student()
    model.eval()
    before = {name: value.detach().clone() for name, value in model.named_parameters()}
    expected_trainable = {
        name for name in before if name.startswith(("classifier.", "bert.encoder.layer.1."))
    }
    forward_modes: list[tuple[bool, bool, int]] = []
    observed_masks: list[set[str]] = []

    def observe_forward(current: Any, args: Any, kwargs: Any) -> None:
        inputs = kwargs["input_ids"] if "input_ids" in kwargs else args[0]
        forward_modes.append((current.training, torch.is_grad_enabled(), len(inputs)))
        observed_masks.append(
            {name for name, value in current.named_parameters() if value.requires_grad}
        )

    records = [
        module.Document(str(index), text, label)
        for index, (text, label) in enumerate(
            [("red square", 0), ("blue circle", 1), ("green triangle", 2)]
        )
    ]
    handle = model.register_forward_pre_hook(observe_forward, with_kwargs=True)
    try:
        history = exercise_call(
            module.adapt_encoder,
            model,
            tokenizer,
            records,
            records,
            module.RunConfig(seed=3, batch_size=2, max_length=8, max_steps=2),
        )
    finally:
        handle.remove()
    assert history.steps == 2
    assert len(history.train_losses) == 2
    assert history.validation_count == 3
    assert history.validation_loss >= 0
    changed = {
        name
        for name, value in model.named_parameters()
        if not torch.equal(before[name], value.detach())
    }
    assert any(name.startswith("classifier.") for name in changed)
    assert any(name.startswith("bert.encoder.layer.1.") for name in changed)
    assert all(name.startswith(("classifier.", "bert.encoder.layer.1.")) for name in changed)
    assert {
        name for name, value in model.named_parameters() if value.requires_grad
    } == expected_trainable
    assert observed_masks
    assert all(mask == expected_trainable for mask in observed_masks)
    assert sum(training and gradients for training, gradients, _ in forward_modes) == 2
    assert (
        sum(size for training, gradients, size in forward_modes if not training and not gradients)
        == 3
    )
    assert all(training == gradients for training, gradients, _ in forward_modes)
    assert model.training is False


def test_saved_student_model_reloads_logits_without_pickle(
    local_model: tuple[Any, Any], tmp_path: Path
) -> None:
    torch = pytest.importorskip("torch")
    model, tokenizer = local_model
    model.eval()
    batch = tokenizer(["red square", "blue circle"], padding=True, return_tensors="pt")
    with torch.inference_mode():
        expected = model(**batch).logits
    restored, restored_tokenizer = exercise_call(
        student().save_and_reload, model, tokenizer, tmp_path / "student-checkpoint"
    )
    with torch.inference_mode():
        actual = restored(
            **restored_tokenizer(["red square", "blue circle"], padding=True, return_tensors="pt")
        ).logits
    assert torch.allclose(actual, expected, atol=1e-6)
    assert not list(tmp_path.rglob("*.bin"))
    assert (tmp_path / "student-checkpoint" / "model.safetensors").is_file()


def test_three_methods_produce_predictions_on_same_test_rows(
    local_model: tuple[Any, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    model, tokenizer = local_model
    source = tmp_path / "local-source"
    model.save_pretrained(source, safe_serialization=True)
    tokenizer.save_pretrained(source)
    module = student()
    # Temporary fixture checks orchestration only, never pretrained quality.
    training = [
        module.Document(str(index), text, label)
        for index, (text, label) in enumerate(
            [
                ("red square", 0),
                ("small red square", 0),
                ("blue circle", 1),
                ("large blue circle", 1),
                ("green triangle", 2),
                ("small green triangle", 2),
                ("large object", 3),
                ("small object", 3),
            ]
        )
    ]
    validation = [
        module.Document("v0", "green object validationonly", 2),
        module.Document("v1", "red circle validationonly", 0),
    ]
    testing = [
        module.Document("t0", "large circle heldoutonly", 3),
        module.Document("t1", "red triangle heldoutonly", 0),
        module.Document("t2", "blue square heldoutonly", 1),
    ]
    vectorizer_fits: list[list[str]] = []
    vectorizers: list[Any] = []
    classifier_fits: list[tuple[int, list[int]]] = []
    prediction_events: dict[int, list[list[int]]] = {}
    current_fit: dict[int, int] = {}
    pooling_batches: list[int] = []
    adaptation_calls: list[tuple[list[str], list[str]]] = []
    frozen_forwards: list[tuple[bool, bool]] = []
    frozen_models: list[tuple[Any, dict[str, Any]]] = []
    original_fit = TfidfVectorizer.fit
    original_fit_transform = TfidfVectorizer.fit_transform
    original_classifier_fit = LogisticRegression.fit
    original_predict = LogisticRegression.predict
    original_pool = module.masked_mean_pool
    original_adapt = module.adapt_encoder
    original_load = transformers.AutoModel.from_pretrained

    def vectorizer_fit(instance: Any, documents: Any, *args: Any, **kwargs: Any) -> Any:
        documents = list(documents)
        vectorizer_fits.append(documents)
        vectorizers.append(instance)
        return original_fit(instance, documents, *args, **kwargs)

    def vectorizer_fit_transform(instance: Any, documents: Any, *args: Any, **kwargs: Any) -> Any:
        documents = list(documents)
        vectorizer_fits.append(documents)
        vectorizers.append(instance)
        return original_fit_transform(instance, documents, *args, **kwargs)

    def classifier_fit(instance: Any, features: Any, labels: Any, *args: Any, **kwargs: Any) -> Any:
        assert features.shape[0] == len(training), "classifier fit must use training rows only"
        classifier_fits.append((features.shape[1], list(labels)))
        current_fit[id(instance)] = len(classifier_fits) - 1
        return original_classifier_fit(instance, features, labels, *args, **kwargs)

    def classifier_predict(instance: Any, features: Any, *args: Any, **kwargs: Any) -> Any:
        actual = original_predict(instance, features, *args, **kwargs)
        if features.shape[0] == len(testing):
            prediction_events.setdefault(current_fit[id(instance)], []).append(actual.tolist())
        return actual

    def pooling(hidden: Any, mask: Any) -> Any:
        assert not torch.is_grad_enabled(), "frozen pooling must use inference/no_grad"
        pooling_batches.append(len(hidden))
        return original_pool(hidden, mask)

    def adapt(current: Any, current_tokenizer: Any, train: Any, valid: Any, config: Any) -> Any:
        adaptation_calls.append(([row.row_id for row in train], [row.row_id for row in valid]))
        return original_adapt(current, current_tokenizer, train, valid, config)

    def load_frozen(*args: Any, **kwargs: Any) -> Any:
        assert kwargs.get("local_files_only") is True
        assert kwargs.get("trust_remote_code") is False
        assert kwargs.get("use_safetensors") is True
        loaded = original_load(*args, **kwargs)
        frozen_models.append(
            (loaded, {name: value.detach().clone() for name, value in loaded.named_parameters()})
        )

        def observe_frozen(current: Any, inputs: Any) -> None:
            frozen_forwards.append((current.training, torch.is_grad_enabled()))

        loaded.register_forward_pre_hook(observe_frozen)
        return loaded

    monkeypatch.setattr(TfidfVectorizer, "fit", vectorizer_fit)
    monkeypatch.setattr(TfidfVectorizer, "fit_transform", vectorizer_fit_transform)
    monkeypatch.setattr(LogisticRegression, "fit", classifier_fit)
    monkeypatch.setattr(LogisticRegression, "predict", classifier_predict)
    monkeypatch.setattr(module, "masked_mean_pool", pooling)
    monkeypatch.setattr(module, "adapt_encoder", adapt)
    monkeypatch.setattr(transformers.AutoModel, "from_pretrained", load_frozen)
    results = exercise_call(
        module.compare_models,
        source,
        {"train": training, "validation": validation, "test": testing},
        module.RunConfig(max_steps=1, batch_size=4, max_length=8),
        tmp_path / "adapted",
    )
    assert_comparison_trace(
        {
            "vectorizer_fits": vectorizer_fits,
            "classifier_fits": classifier_fits,
            "tfidf_width": len(vectorizers[0].vocabulary_) if vectorizers else 0,
            "pooling_batches": pooling_batches,
            "adaptation_calls": adaptation_calls,
            "frozen_forwards": frozen_forwards,
            "frozen_unchanged": all(
                torch.equal(before[name], value.detach())
                for frozen, before in frozen_models
                for name, value in frozen.named_parameters()
            ),
            "prediction_events": prediction_events,
        },
        results,
        training,
        validation,
        testing,
    )
    protocol_module = importlib.import_module(f"{PACKAGE}.protocol")
    protocol_module.validate_comparison(results, [3, 0, 1])
    assert (tmp_path / "adapted" / "model.safetensors").is_file()
    assert (
        protocol_module.checkpoint_predictions(
            tmp_path / "adapted", [row.text for row in testing], batch_size=4, max_length=8
        )
        == results["adapted_encoder"]["predictions"]
    )


def test_comparison_contract_rejects_a_constant_counterfeit(
    local_model: tuple[Any, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sklearn.metrics import accuracy_score, f1_score

    model, tokenizer = local_model

    def counterfeit(
        source: Path, splits: Any, config: Any, output: Path
    ) -> dict[str, dict[str, object]]:
        # Deliberately wrong test-only counterexample: no fit, pooling or adaptation.
        model.save_pretrained(output, safe_serialization=True)
        tokenizer.save_pretrained(output)
        labels = [document.label for document in splits["test"]]
        predictions = [0] * len(labels)
        return {
            name: {
                "predictions": predictions,
                "accuracy": float(accuracy_score(labels, predictions)),
                "macro_f1": float(
                    f1_score(
                        labels, predictions, labels=[0, 1, 2, 3], average="macro", zero_division=0
                    )
                ),
                "warm_seconds": 0.01,
                "peak_memory_bytes": None,
                "memory_note": "NOT_MEASURED: adversarial fixture",
            }
            for name in ("tfidf_linear", "frozen_embeddings", "adapted_encoder")
        }

    monkeypatch.setattr(student(), "compare_models", counterfeit)
    with pytest.raises(AssertionError):
        test_three_methods_produce_predictions_on_same_test_rows(local_model, tmp_path, monkeypatch)


def test_adaptation_contract_rejects_changes_without_training_modes(
    local_model: tuple[Any, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    torch = pytest.importorskip("torch")
    module = student()

    def counterfeit(model: Any, tokenizer: Any, train: Any, validation: Any, config: Any) -> Any:
        # Deliberately wrong: synthetic weight changes bypass training and validation.
        with torch.no_grad():
            for name, value in model.named_parameters():
                if name.startswith(("classifier.", "bert.encoder.layer.1.")):
                    value.add_(0.01)
        model.eval()
        return module.TrainingHistory(2, (0.1, 0.1), 0.1, 3)

    monkeypatch.setattr(module, "adapt_encoder", counterfeit)
    with pytest.raises(AssertionError):
        test_adaptation_updates_only_last_block_and_head(local_model)


def test_required_offline_artifacts_are_present_and_valid() -> None:
    module = importlib.import_module(f"{PACKAGE}.protocol")
    output = Path(__file__).resolve().parents[2] / "generated-reports" / "huggingface"
    if not (output / "offline-report.json").exists():
        pytest.xfail("Student offline report is absent; run and explain your own experiment")
    module.validate_offline_artifacts(output)
