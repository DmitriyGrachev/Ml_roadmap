"""Tiny random SentenceTransformer mechanism; intentionally no general learner solution."""

from importlib import import_module
from pathlib import Path
from typing import Any


def tiny_model(directory: Path) -> Any:
    """One random Transformer+mean Pooling; no Hub, pretrained claim or integrations."""
    torch = import_module("torch")
    hf = import_module("transformers")
    st = import_module("sentence_transformers")
    modules = import_module("sentence_transformers.sentence_transformer.modules")
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
        hidden_dropout_prob=0.0,
        attention_probs_dropout_prob=0.0,
    )
    hf.BertModel(config).save_pretrained(str(directory), safe_serialization=True)
    encoder = modules.Transformer(
        str(directory),
        model_kwargs={"local_files_only": True},
        processor_kwargs={"local_files_only": True},
        max_seq_length=32,
    )
    return st.SentenceTransformer(
        modules=[encoder, modules.Pooling(16, pooling_mode="mean")], device="cpu"
    )


def smoke(directory: Path) -> dict[str, Any]:
    """Fixed two-row, two-update mechanism, deliberately not a reusable fit function."""
    torch = import_module("torch")
    st = import_module("sentence_transformers")
    losses = import_module("sentence_transformers.sentence_transformer.losses")
    model = tiny_model(directory / "initial")
    before = [p.detach().clone() for p in model.parameters()]
    objective = losses.TripletLoss(
        model, distance_metric=losses.TripletDistanceMetric.COSINE, triplet_margin=0.2
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    gradient_norm = 0.0
    model.train()
    for _ in range(2):
        optimizer.zero_grad()
        features = [
            model.tokenize(texts)
            for texts in (
                ["printer paper", "scan settings"],
                ["paper printer", "settings scan"],
                ["scan settings", "printer paper"],
            )
        ]
        loss = objective(features, torch.zeros(2))
        if not torch.isfinite(loss):
            raise ValueError("nonfinite random smoke loss")
        loss.backward()
        gradient_norm = float(
            sum(p.grad.detach().abs().sum() for p in model.parameters() if p.grad is not None)
        )
        optimizer.step()
    change = float(
        sum(
            (old - new.detach()).abs().sum()
            for old, new in zip(before, model.parameters(), strict=True)
        )
    )
    model.eval()
    checkpoint = directory / "checkpoint"
    model.save_pretrained(str(checkpoint), safe_serialization=True)
    reloaded = st.SentenceTransformer(
        str(checkpoint), local_files_only=True, device="cpu", trust_remote_code=False
    )
    expected = model.encode(
        ["printer paper", "scan settings"],
        normalize_embeddings=True,
        convert_to_tensor=True,
        show_progress_bar=False,
    )
    actual = reloaded.encode(
        ["printer paper", "scan settings"],
        normalize_embeddings=True,
        convert_to_tensor=True,
        show_progress_bar=False,
    )
    return {
        "evidence_kind": "AUTHOR_RANDOM_API_SMOKE",
        "steps": 2,
        "gradient_norm": gradient_norm,
        "parameter_change": change,
        "reload_max_error": float((expected - actual).abs().max()),
    }
