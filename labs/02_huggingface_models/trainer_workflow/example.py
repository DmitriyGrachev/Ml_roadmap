"""Fixed, random local BERT/Trainer demonstration; never learner credit."""

from __future__ import annotations

import hashlib
import json
from importlib import import_module
from pathlib import Path
from typing import Any


def model_identity(model: Any) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def local_components(directory: Path) -> tuple[Any, Any]:
    transformers = import_module("transformers")

    directory.mkdir(parents=True, exist_ok=False)
    vocabulary = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "red", "blue", "square"]
    tokenizer = transformers.BertTokenizerFast(vocab={word: i for i, word in enumerate(vocabulary)})
    tokenizer.save_pretrained(directory)
    model = transformers.BertForSequenceClassification(
        transformers.BertConfig(
            vocab_size=len(vocabulary),
            hidden_size=16,
            num_hidden_layers=1,
            num_attention_heads=2,
            intermediate_size=24,
            max_position_embeddings=64,
            num_labels=2,
            id2label={0: "RED", 1: "BLUE"},
            label2id={"RED": 0, "BLUE": 1},
        )
    )
    return model, tokenizer


def run_example(output: Path) -> dict[str, Any]:
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    Dataset = import_module("datasets").Dataset

    torch.set_num_threads(1)
    set_seed(17)
    output.mkdir(parents=True, exist_ok=False)
    model, tokenizer = local_components(output / "tokenizer")
    train = Dataset.from_list(
        [
            {"id": f"t{i}", "text": text, "label": i % 2}
            for i, text in enumerate(["red", "blue square", "red square", "blue"])
        ]
    )
    validation = Dataset.from_list(
        [{"id": "v0", "text": "red square", "label": 0}, {"id": "v1", "text": "blue", "label": 1}]
    )

    def encode(batch: Any) -> dict[str, Any]:
        return {
            **tokenizer(batch["text"], truncation=True, max_length=16),
            "labels": batch["label"],
        }

    encoded_train = train.map(encode, batched=True, remove_columns=train.column_names)
    encoded_validation = validation.map(
        encode, batched=True, remove_columns=validation.column_names
    )

    def metrics(evaluation: Any) -> dict[str, float]:
        return {
            "accuracy": float((evaluation.predictions.argmax(-1) == evaluation.label_ids).mean())
        }

    def arguments(directory: Path, steps: int) -> Any:
        return TrainingArguments(
            output_dir=str(directory),
            max_steps=steps,
            per_device_train_batch_size=2,
            per_device_eval_batch_size=2,
            learning_rate=0.0005,
            use_cpu=True,
            eval_strategy="steps",
            eval_steps=1,
            save_strategy="steps",
            save_steps=1,
            logging_steps=1,
            load_best_model_at_end=True,
            metric_for_best_model="accuracy",
            greater_is_better=True,
            save_total_limit=2,
            report_to="none",
            disable_tqdm=True,
            dataloader_pin_memory=False,
            seed=17,
            optim="adamw_torch",
        )

    trainer = Trainer(
        model=model,
        args=arguments(output / "run", 2),
        train_dataset=encoded_train,
        eval_dataset=encoded_validation,
        data_collator=DataCollatorWithPadding(tokenizer),
        processing_class=tokenizer,
        compute_metrics=metrics,
    )
    trainer.train()
    history = [dict(row) for row in trainer.state.log_history if "eval_accuracy" in row]
    final = output / "final"
    trainer.save_model(str(final))
    tokenizer.save_pretrained(final)
    loaded = AutoModelForSequenceClassification.from_pretrained(
        final, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    reloaded_tokenizer = AutoTokenizer.from_pretrained(
        final, local_files_only=True, trust_remote_code=False
    )
    model.eval()
    batch = reloaded_tokenizer(["red square", "blue"], padding=True, return_tensors="pt")
    with torch.inference_mode():
        difference = float((model(**batch).logits - loaded(**batch).logits).abs().max())
    resumed = Trainer(
        model=loaded,
        args=arguments(output / "resumed", 3),
        train_dataset=encoded_train,
        eval_dataset=encoded_validation,
        data_collator=DataCollatorWithPadding(tokenizer),
        processing_class=tokenizer,
        compute_metrics=metrics,
    )
    # Capture identity before resumed.train mutates loaded.
    identity, reload_identity = model_identity(model), model_identity(loaded)
    resumed.train(resume_from_checkpoint=trainer.state.best_model_checkpoint)
    return {
        "evidence": "RANDOM_LOCAL_MECHANICS_ONLY",
        "history": history,
        "best_metric": trainer.state.best_metric,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "global_step": trainer.state.global_step,
        "resumed_step": resumed.state.global_step,
        "model_identity": identity,
        "reload_identity": reload_identity,
        "reload_max_abs": difference,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/trainer-author-smoke"))
    print(json.dumps(run_example(parser.parse_args().output), indent=2))
