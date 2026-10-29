"""Fixed annotated random-BERT loss/collation smoke, not pretrained NER."""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Any


def run_example(output: Path) -> dict[str, Any]:
    import torch

    transformers = import_module("transformers")

    torch.set_num_threads(1)
    transformers.set_seed(19)
    output.mkdir(parents=True, exist_ok=False)
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
    # Deliberately explicit fixed annotations, independent of learner align_labels.
    first = tokenizer(["Ada", "visits", "Rome", "."], is_split_into_words=True)
    second = tokenizer(["Lee", "."], is_split_into_words=True)
    assert first.word_ids() == [None, 0, 0, 1, 2, 3, None]
    first["labels"] = [-100, 1, -100, 0, 3, 0, -100]
    second["labels"] = [-100, 1, 0, -100]
    batch = transformers.DataCollatorForTokenClassification(tokenizer, label_pad_token_id=-100)(
        [first, second]
    )
    labels = {0: "O", 1: "B-PER", 2: "I-PER", 3: "B-LOC", 4: "I-LOC"}
    model = transformers.BertForTokenClassification(
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
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0005)
    model.train()
    result = model(**batch)
    loss = result.loss
    if not bool(torch.isfinite(loss)):
        raise ValueError("nonfinite loss")
    loss.backward()
    optimizer.step()
    model.eval()
    final = output / "final"
    model.save_pretrained(final, safe_serialization=True)
    tokenizer.save_pretrained(final)
    loaded = transformers.AutoModelForTokenClassification.from_pretrained(
        final, local_files_only=True, trust_remote_code=False, use_safetensors=True
    ).eval()
    loaded_tokenizer = transformers.AutoTokenizer.from_pretrained(
        final, local_files_only=True, trust_remote_code=False
    )
    inputs = loaded_tokenizer("Ada visits Rome.", return_tensors="pt")
    with torch.inference_mode():
        difference = float((model(**inputs).logits - loaded(**inputs).logits).abs().max())
    return {
        "evidence": "RANDOM_LOCAL_MECHANICS_ONLY",
        "finite_loss": True,
        "loss": float(loss.detach()),
        "reload_max_abs": difference,
        "labels": batch["labels"].tolist(),
        "padding_ignored": bool((batch["labels"][1, 4:] == -100).all()),
        "word_ids": first.word_ids(),
        "optimizer_steps": 1,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/ner-author-smoke"))
    print(json.dumps(run_example(parser.parse_args().output), indent=2))
