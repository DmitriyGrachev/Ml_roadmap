"""Worked single-sequence causal-LM targets; not a tokenizer or training pipeline."""

from __future__ import annotations

from collections.abc import Sequence


def causal_targets(
    input_ids: Sequence[int],
    attention_mask: Sequence[int],
    labels: Sequence[int],
) -> list[tuple[int, int]]:
    """Return (logit position, target ID) for a right-padded, unshifted toy sequence."""
    if len(input_ids) < 2 or not len(input_ids) == len(attention_mask) == len(labels):
        raise ValueError("all sequences need equal length >= 2")
    if any(type(token) is not int or token < 0 for token in input_ids):
        raise ValueError("token IDs must be nonnegative integers")
    if any(type(mask) is not int or mask not in (0, 1) for mask in attention_mask):
        raise ValueError("attention mask must contain integer 0 or 1")
    if any(type(label) is not int or label < -100 for label in labels):
        raise ValueError("target labels must be integer IDs or -100")
    if labels[0] != -100:
        raise ValueError("first position has no previous logit; mask its target")
    padding_started = False
    pairs = []
    for position, (token, mask, label) in enumerate(
        zip(input_ids, attention_mask, labels, strict=True)
    ):
        if mask == 0:
            padding_started = True
            if label != -100:
                raise ValueError("padding must not supply a target")
        elif padding_started:
            raise ValueError("this toy contract supports right padding only")
        if label != -100:
            if label != token:
                raise ValueError("unshifted target must match its input token ID")
            pairs.append((position - 1, label))
    if not pairs:
        raise ValueError("sequence has no next-token targets")
    return pairs


if __name__ == "__main__":
    print(causal_targets([1, 2, 7, 3, 8, 4], [1] * 6, [-100] * 4 + [8, 4]))
