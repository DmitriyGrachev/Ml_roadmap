"""Opt-in real PEFT checks: masks, frozen base, offline fresh reload and corruption."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

import pytest

if os.environ.get("ROADMAP_RUN_PEFT") != "1":
    pytest.skip(
        "set ROADMAP_RUN_PEFT=1 in the opt-in finetuning environment", allow_module_level=True
    )

missing = [
    name
    for name in ("torch", "peft", "transformers", "safetensors")
    if importlib.util.find_spec(name) is None
]
if missing:
    raise RuntimeError(
        "ROADMAP_RUN_PEFT=1 requires the finetuning environment; missing: " + ", ".join(missing)
    )
import torch  # noqa: E402 -- optional gate must run before importing training dependencies


def module() -> Any:
    path = Path(__file__).with_name("peft_demo.py")
    assert path.is_file(), "actual offline PEFT lifecycle demo missing"
    return importlib.import_module("labs.04_llm_finetuning.peft_demo")


def deny_connection(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("network access attempted")


def test_prompt_padding_and_internal_shift_match_explicit_loss() -> None:
    demo = module()
    batch = demo.make_batch(demo.EXAMPLES[:2])
    assert batch["labels"][0].tolist() == [-100, -100, -100, -100, 5, 2, -100]
    assert batch["attention_mask"][0].tolist() == [1, 1, 1, 1, 1, 1, 0]
    model = demo.make_base()
    model.eval()
    with torch.inference_mode():
        result = model(**batch)
    expected = torch.nn.functional.cross_entropy(
        result.logits[:, :-1].reshape(-1, len(demo.VOCAB)),
        batch["labels"][:, 1:].reshape(-1),
        ignore_index=-100,
    )
    torch.testing.assert_close(result.loss, expected)


def test_word_groups_do_not_leak_between_splits() -> None:
    groups: dict[str, str] = {}
    for example in module().EXAMPLES:
        word, split = example["answer"], example["split"]
        assert word not in groups or groups[word] == split
        groups[word] = split


@pytest.fixture(scope="module")
def experiment(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    path = tmp_path_factory.mktemp("peft") / "run"
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket.socket, "connect", deny_connection)
        patch.setattr(socket, "create_connection", deny_connection)
        return path, module().run_experiment(path)


def test_only_lora_updates_and_fresh_process_reproduces_logits(
    experiment: tuple[Path, dict[str, Any]],
) -> None:
    path, report = experiment
    assert report["base_unchanged"] is True
    assert report["frozen_gradients_absent"] is True
    assert report["changed_adapter_parameters"] > 0
    assert report["fresh_process"]["logits_equal"] is True
    assert report["fresh_process"]["predictions_equal"] is True
    assert report["initial"]["validation"]["target_tokens"] == 4
    assert report["adapted"]["test"]["target_tokens"] == 4
    assert report["trainable_parameters"] < report["frozen_parameters"]
    assert (path / "base/model.safetensors").is_file()
    assert (path / "adapter/adapter_model.safetensors").is_file()
    assert len(report["history"]) == report["training_config"]["steps"]
    ids = json.loads((path / "data.json").read_text(encoding="utf-8"))
    assert len({row["id"] for row in ids}) == len(ids)
    splits = [
        {row["id"] for row in ids if row["split"] == s} for s in ("train", "validation", "test")
    ]
    assert not splits[0] & splits[1]
    assert not splits[0] & splits[2]
    assert not splits[1] & splits[2]


@pytest.mark.parametrize(
    "relative",
    [
        "base/model.safetensors",
        "base/config.json",
        "adapter/adapter_model.safetensors",
        "vocab.json",
        "data.json",
        "source_identity.json",
    ],
)
def test_tampered_bundle_is_rejected_before_loading(
    experiment: tuple[Path, dict[str, Any]], tmp_path: Path, relative: str
) -> None:
    source, _ = experiment
    altered = tmp_path / "altered"
    shutil.copytree(source, altered)
    with (altered / relative).open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="identity"):
        module().load_bundle(altered)


def test_different_base_same_architecture_is_rejected(
    experiment: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    source, _ = experiment
    altered = tmp_path / "other-base"
    shutil.copytree(source, altered)
    torch.manual_seed(999)
    module().make_base().save_pretrained(altered / "base", safe_serialization=True)
    with pytest.raises(ValueError, match="identity"):
        module().load_bundle(altered)


def test_existing_output_is_preserved(experiment: tuple[Path, dict[str, Any]]) -> None:
    path, _ = experiment
    previous = (path / "report.json").read_bytes()
    with pytest.raises(FileExistsError):
        module().run_experiment(path)
    assert (path / "report.json").read_bytes() == previous


@pytest.mark.parametrize("relative", ["base/adapter_config.json", "adapter/model.safetensors"])
def test_unlisted_consumer_file_is_rejected(
    experiment: tuple[Path, dict[str, Any]], tmp_path: Path, relative: str
) -> None:
    source, _ = experiment
    altered = tmp_path / "extra-file"
    shutil.copytree(source, altered)
    (altered / relative).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory"):
        module().load_bundle(altered)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_model_directory_junction_is_rejected(
    experiment: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    source, _ = experiment
    altered = tmp_path / "junction-bundle"
    shutil.copytree(source, altered, ignore=shutil.ignore_patterns("base"))
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(altered / "base"), str(source / "base")],
        check=True,
        capture_output=True,
    )
    with pytest.raises(ValueError, match="real base directory"):
        module().load_bundle(altered)


def test_reload_is_offline(
    experiment: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(socket.socket, "connect", deny_connection)
    monkeypatch.setattr(socket, "create_connection", deny_connection)
    path, _ = experiment
    assert module().verify_bundle(path)["logits_equal"] is True
