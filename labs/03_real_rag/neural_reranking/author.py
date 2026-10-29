"""Random local API mechanism only; never a learner implementation or quality claim."""

from importlib import import_module
from pathlib import Path
from typing import Any


def tiny_model(directory: Path) -> Any:
    """Save one-layer random BERT + local vocab, then load the real CrossEncoder."""
    torch = import_module("torch")
    hf = import_module("transformers")
    torch.set_num_threads(1)
    torch.manual_seed(7)
    directory.mkdir(parents=True, exist_ok=False)
    vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "printer", "paper", "scan", "settings"]
    (directory / "vocab.txt").write_text("\n".join(vocab) + "\n", encoding="utf-8")
    hf.BertTokenizer(vocab=str(directory / "vocab.txt"), do_lower_case=True).save_pretrained(
        str(directory)
    )
    config = hf.BertConfig(
        vocab_size=len(vocab),
        hidden_size=16,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=24,
        max_position_embeddings=64,
        num_labels=1,
        hidden_dropout_prob=0.0,
        attention_probs_dropout_prob=0.0,
    )
    hf.BertForSequenceClassification(config).save_pretrained(
        str(directory), safe_serialization=True
    )
    return import_module(__package__ + ".runtime").local_scorer(directory)
