"""Two fixed views of text/attention mechanics; local random weights, not quality."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any

import torch
import transformers
from torch.nn import functional as functional

from .example import make_local_components, run_smoke


def fixed_attention() -> dict[str, Any]:
    """Hand arithmetic for ONE fixed row, checked against library SDPA, not a solver."""
    q = torch.tensor([[[[1.0, 0.0]]]], dtype=torch.float64, requires_grad=True)
    k = torch.tensor(
        [[[[math.sqrt(2), 0.0], [0.0, 0.0], [9.0, 9.0]]]], dtype=torch.float64, requires_grad=True
    )
    v = torch.tensor(
        [[[[2.0, 0.0], [0.0, 4.0], [900.0, 900.0]]]], dtype=torch.float64, requires_grad=True
    )
    allowed = torch.tensor([[[[True, True, False]]]])
    scores = (q.detach() @ k.detach().transpose(-2, -1)) / math.sqrt(2)
    # Closed-form hand calculation for the two allowed scores [1, 0].
    p0 = math.exp(1) / (math.exp(1) + 1)
    p1 = 1 / (math.exp(1) + 1)
    hand_output = torch.tensor([2 * p0, 4 * p1], dtype=torch.float64)
    output = functional.scaled_dot_product_attention(q, k, v, attn_mask=allowed, dropout_p=0.0)
    torch.autograd.backward(output.sum())
    assert q.grad is not None
    assert k.grad is not None
    assert v.grad is not None
    with torch.no_grad():
        masked_change = v.clone()
        masked_change[0, 0, 2] = -9000.0
        ignored = functional.scaled_dot_product_attention(
            q, k, masked_change, attn_mask=allowed, dropout_p=0.0
        )
        allowed_change = v.clone()
        allowed_change[0, 0, 0, 0] += 1.0
        affected = functional.scaled_dot_product_attention(
            q, k, allowed_change, attn_mask=allowed, dropout_p=0.0
        )
    return {
        "shapes": {
            "q": list(q.shape),
            "k": list(k.shape),
            "v": list(v.shape),
            "allowed": list(allowed.shape),
            "output": list(output.shape),
        },
        "scaled_scores": scores.flatten().tolist(),
        "masked_scores": [scores.flatten()[0].item(), scores.flatten()[1].item(), "-inf"],
        "weights": [p0, p1, 0.0],
        "output": output.detach().flatten().tolist(),
        "manual_max_difference": (output.detach().flatten() - hand_output).abs().max().item(),
        "masked_value_change_max_difference": (output.detach() - ignored).abs().max().item(),
        "allowed_value_change_max_difference": (output.detach() - affected).abs().max().item(),
        "grad_q": q.grad[0, 0].tolist(),
        "grad_k": k.grad[0, 0].tolist(),
        "grad_v": v.grad[0, 0].tolist(),
    }


def text_trace() -> dict[str, Any]:
    """Trace the existing random BERT fixture; no Hub identifier is loaded."""
    model, tokenizer = make_local_components()
    model.eval()
    texts = ["red", "large blue square"]
    batch = tokenizer(texts, padding=True, truncation=True, max_length=8, return_tensors="pt")
    with torch.inference_mode():
        lookup = model.bert.embeddings.word_embeddings(batch["input_ids"])
        embeddings = model.bert.embeddings(
            input_ids=batch["input_ids"], token_type_ids=batch["token_type_ids"]
        )
        encoded = model.bert(**batch)
        logits = model(**batch).logits
        pooler_formula = torch.tanh(model.bert.pooler.dense(encoded.last_hidden_state[:, 0]))
        reconstructed_head = model.classifier(model.dropout(encoded.pooler_output))
        changed = {name: value.clone() for name, value in batch.items()}
        changed["input_ids"][0, 3:] = torch.tensor([7, 10])
        masked_logits = model(**changed).logits
        changed["attention_mask"][0, 3:] = 1
        unmasked_logits = model(**changed).logits
        single = tokenizer([texts[0]], return_tensors="pt")
        single_logits = model(**single).logits
    return {
        "texts": texts,
        "initialization_seed": 17,  # Seed fixed by the existing local factory in example.py.
        "tokens": [tokenizer.convert_ids_to_tokens(row) for row in batch["input_ids"].tolist()],
        "input_ids": batch["input_ids"].tolist(),
        "attention_mask": batch["attention_mask"].tolist(),
        "token_type_ids": batch["token_type_ids"].tolist(),
        "input_dtype": str(batch["input_ids"].dtype),
        "shapes": {
            "word_lookup": list(lookup.shape),
            "embeddings": list(embeddings.shape),
            "hidden": list(encoded.last_hidden_state.shape),
            "pooler": list(encoded.pooler_output.shape),
            "logits": list(logits.shape),
        },
        "logits": logits.tolist(),
        "probabilities": logits.softmax(dim=-1).tolist(),
        "selected_class_indices": logits.argmax(dim=-1).tolist(),
        "pooler_formula_max_difference": (encoded.pooler_output - pooler_formula)
        .abs()
        .max()
        .item(),
        "head_max_difference": (logits - reconstructed_head).abs().max().item(),
        "masked_id_change_max_difference": (logits - masked_logits).abs().max().item(),
        "unmasked_id_change_max_difference": (logits - unmasked_logits).abs().max().item(),
        "single_vs_batch_max_difference": (single_logits[0] - logits[0]).abs().max().item(),
        "truncated_ids": tokenizer(texts[1], truncation=True, max_length=4)["input_ids"],
        "unknown_ids": tokenizer("purple")["input_ids"],
        "config": json.loads(model.config.to_json_string(use_diff=False)),
        "pretrained_quality": "NOT_RUN",
    }


def run_walkthrough(directory: Path, *, plots: bool = False) -> dict[str, Any]:
    """Persist only teacher artifacts to a new directory; keep learner state intact."""
    directory.mkdir(parents=True, exist_ok=False)
    with torch.random.fork_rng(devices=[]):
        text = text_trace()
        identity = json.dumps(
            {
                "texts": text["texts"],
                "input_ids": text["input_ids"],
                "split": "NOT_APPLICABLE_MECHANICS_ONLY",
            },
            sort_keys=True,
        ).encode()
        result: dict[str, Any] = {
            "evidence": "LOCAL_RANDOM_ENCODER_AND_FIXED_ATTENTION_ONLY",
            "quality_claim": False,
            "versions": {
                "python": platform.python_version(),
                "torch": torch.__version__,
                "transformers": transformers.__version__,
            },
            "source_sha256": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (Path(__file__), Path(__file__).with_name("example.py"))
            },
            "data_identity": hashlib.sha256(identity).hexdigest(),
            "attention": fixed_attention(),
            "text": text,
            "smoke": run_smoke(directory / "local-model"),
            "plots": ["attention.png"] if plots else [],
        }
    if plots:
        from matplotlib.figure import Figure

        figure = Figure(figsize=(7.2, 3.5), layout="constrained")
        axis = figure.subplots()
        weights = result["attention"]["weights"]
        matrix = axis.imshow([weights], vmin=0, vmax=1, cmap="Blues", aspect="auto")
        for index, value in enumerate(weights):
            axis.text(
                index,
                0,
                f"{value:.6f}" + ("\nMASKED" if index == 2 else ""),
                ha="center",
                va="center",
                color="white" if value > 0.5 else "black",
            )
        axis.set(
            xticks=[0, 1, 2],
            xticklabels=["key 0 (allowed)", "key 1 (allowed)", "key 2 (blocked)"],
            yticks=[0],
            yticklabels=["query 0"],
            xlabel="Key position",
            title="Fixed attention row: weights, not a causal explanation",
        )
        figure.colorbar(matrix, ax=axis, label="Softmax weight")
        figure.savefig(directory / "attention.png", dpi=150)
    (directory / "trace.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plots", action="store_true")
    arguments = parser.parse_args()
    result = run_walkthrough(arguments.output, plots=arguments.plots)
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "attention": result["attention"]["output"],
                "logits_shape": result["text"]["shapes"]["logits"],
                "quality_claim": False,
            }
        )
    )


if __name__ == "__main__":
    main()
