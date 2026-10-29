"""Read-only check of actual Trainer batches/loss; never a learner implementation."""

from collections import Counter
from typing import Any


def verify_training_batches(trainer: Any, rows: list[dict[str, list[int]]]) -> Any:
    """Check every local batch against expected rows, independent of shuffle order.

    No optimizer/backward call. Check the trainer's own compute_loss, not merely a
    separate collator or a reconstructed model loss. Restore the caller's mode.
    """
    import torch

    fields = ("input_ids", "attention_mask", "labels")
    expected = Counter(tuple(tuple(row[field]) for field in fields) for row in rows)
    observed: Counter[tuple[tuple[int, ...], ...]] = Counter()
    model = trainer.model
    if not isinstance(model, torch.nn.Module):
        raise TypeError("trainer model must be a torch module")
    original_mode = model.training
    first = None
    try:
        model.eval()
        for batch in trainer.get_train_dataloader():
            if not all(field in batch for field in fields):
                raise ValueError("actual training batch is missing IDs/attention/labels")
            if not all(batch[field].ndim == 2 for field in fields):
                raise ValueError("actual training batch must contain rank-two tensors")
            if not all(batch[field].shape == batch["input_ids"].shape for field in fields):
                raise ValueError("actual training batch shapes differ")
            for i in range(batch["input_ids"].shape[0]):
                identity = tuple(tuple(batch[field][i].tolist()) for field in fields)
                if identity not in expected:
                    raise ValueError("actual training batch changed expected IDs/attention/labels")
                observed[identity] += 1
            # The values already match the independent expected rows exactly.
            # Keep labels isolated from any mutation in compute_loss.
            labels = batch["labels"].detach().clone()
            with torch.no_grad():
                logits = model(
                    input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]
                ).logits
                manual = torch.nn.functional.cross_entropy(
                    logits[:, :-1].reshape(-1, logits.shape[-1]),
                    labels[:, 1:].reshape(-1),
                    ignore_index=-100,
                )
                actual = trainer.compute_loss(model, {k: v.clone() for k, v in batch.items()})
            if not torch.isfinite(manual) or not torch.isfinite(actual):
                raise ValueError("actual trainer causal loss must be finite")
            torch.testing.assert_close(actual, manual, atol=1e-6, rtol=1e-5)
            if first is None:
                first = batch
    finally:
        model.train(original_mode)
    if observed != expected or first is None:
        raise ValueError("actual training loader must cover every expected row exactly once")
    return first
