"""Tokenizer-only regressions: no weights, training, downloads or learner evidence."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from projects.external_tabular.evidence import sha256

from .protocol import validate_checkpoint_inventory


@pytest.fixture
def saved_tokenizers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    transformers = pytest.importorskip("transformers")
    vocabulary = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "red", "blue", "circle"]
    tokenizer = transformers.BertTokenizer(vocab={word: i for i, word in enumerate(vocabulary)})
    base, adapted = tmp_path / "base", tmp_path / "adapted"
    tokenizer.save_pretrained(base)
    tokenizer(["RED", "blue circle"], padding=True, truncation=True, max_length=64)
    tokenizer.save_pretrained(adapted)
    assert sha256(base / "tokenizer.json") != sha256(adapted / "tokenizer.json")
    # Inventory-only dummy bytes; no model loader is called in these tokenizer tests.
    for directory in (base, adapted):
        (directory / "model.safetensors").write_bytes(b"test-owned-no-weights")
        (directory / "config.json").write_text('{"model_type":"bert"}', encoding="utf-8")
    specs = [
        {"filename": path.name, "sha256": sha256(path), "size_bytes": path.stat().st_size}
        for path in base.iterdir()
    ]
    monkeypatch.setattr(
        importlib.import_module("labs.02_huggingface_models.download"),
        "resource_manifest",
        lambda: {"model": {"files": specs}},
    )
    return tmp_path, inventory(tmp_path)


def inventory(root: Path) -> dict[str, Any]:
    files = {
        path.relative_to(root).as_posix(): path
        for directory in (root / "base", root / "adapted")
        for path in directory.iterdir()
    }
    return {
        "manifest": {"artifacts": {logical: {"path": logical} for logical in files}},
        "files": files,
    }


def test_normal_encode_save_reload_preserves_effective_tokenizer(
    saved_tokenizers: tuple[Path, dict[str, Any]],
) -> None:
    root, result = saved_tokenizers
    assert validate_checkpoint_inventory(root, result) == (root / "base", root / "adapted")


@pytest.mark.parametrize(
    "change",
    ["vocabulary", "added_token", "normalizer", "special_token", "padding_side", "truncation_side"],
)
def test_changed_effective_tokenizer_is_rejected(
    saved_tokenizers: tuple[Path, dict[str, Any]],
    change: str,
) -> None:
    root, _ = saved_tokenizers
    path = root / "adapted" / "tokenizer.json"
    if change == "added_token":
        transformers = importlib.import_module("transformers")
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            root / "adapted", local_files_only=True, trust_remote_code=False
        )
        tokenizer.add_tokens(["new-token"])
        tokenizer.save_pretrained(root / "adapted")
    if change in {"padding_side", "truncation_side", "special_token", "normalizer"}:
        path = path.with_name("tokenizer_config.json")
    value = json.loads(path.read_text(encoding="utf-8"))
    if change == "vocabulary":
        value["model"]["vocab"]["red"], value["model"]["vocab"]["blue"] = (
            value["model"]["vocab"]["blue"],
            value["model"]["vocab"]["red"],
        )
    elif change == "normalizer":
        # BertTokenizer reconstructs its normalizer from this auxiliary setting.
        value["do_lower_case"] = False
    elif change == "special_token":
        value["pad_token"] = "[CLS]"
    elif change != "added_token":
        value[change] = "left"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="tokenizer"):
        validate_checkpoint_inventory(root, inventory(root))
