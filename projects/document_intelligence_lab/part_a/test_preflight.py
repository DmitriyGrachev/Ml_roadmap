"""Operator input checks use real A1 bundles and deliberately fake encoder bytes."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

import pytest

from ..artifacts import file_sha256, read_json
from ..part_a1.demo import run_demo
from .protocol import register_checkpoint, verify_comparison_inputs


@pytest.fixture
def inputs(tmp_path: Path) -> dict[str, Any]:
    run = run_demo(tmp_path / "a1")
    reference = read_json(run / "rules" / "manifest.json")
    encoder = tmp_path / "encoder"
    encoder.mkdir()
    (encoder / "config.json").write_text(
        json.dumps(
            {
                "id2label": dict(enumerate(reference["labels"])),
                "max_position_embeddings": 16,
            }
        ),
        encoding="utf-8",
    )
    (encoder / "tokenizer.json").write_text("{}", encoding="utf-8")
    (encoder / "model.safetensors").write_bytes(b"FAKE inventory bytes, not a runnable model")
    digest = register_checkpoint(
        encoder,
        labels=reference["labels"],
        dataset_sha256=reference["dataset_sha256"],
        split_sha256=reference["split_sha256"],
        source_revision="operator-local-fixture",
        evidence_kind="teacher-random",
        max_length=8,
    )
    return {
        "rules": run / "rules",
        "rules_sha256": file_sha256(run / "rules" / "manifest.json"),
        "tfidf": run / "tfidf-linear",
        "tfidf_sha256": file_sha256(run / "tfidf-linear" / "manifest.json"),
        "encoder": encoder,
        "encoder_sha256": digest,
        "seed": 17,
        "device": "cpu",
        "max_seconds": 60.0,
        "max_memory_mib": 512,
    }


def preflight_module() -> Any:
    assert Path(__file__).with_name("preflight.py").is_file(), "Input preflight is missing"
    return importlib.import_module("projects.document_intelligence_lab.part_a.preflight")


def test_valid_inputs_report_shared_cohort_without_claiming_execution(
    inputs: dict[str, Any],
) -> None:
    report = preflight_module().preflight(**inputs)
    assert report["status"] == "INPUTS_VERIFIED"
    assert report["execution"] == "NOT_RUN"
    assert report["quality"] == "NOT_EVALUATED"
    assert report["requested_settings"] == {
        "seed": 17,
        "device": "cpu",
        "max_seconds": 60.0,
        "max_memory_mib": 512,
    }
    reference = read_json(inputs["rules"] / "manifest.json")
    assert report["dataset_sha256"] == reference["dataset_sha256"]
    assert report["split_sha256"] == reference["split_sha256"]
    assert report["labels"] == ["circle", "square", "triangle"]
    assert report["evaluation_ids"] == ["s16", "s17", "s18", "s19", "s20", "s21"]
    assert report["manifest_pins"] == {
        "rules": inputs["rules_sha256"],
        "tfidf-linear": inputs["tfidf_sha256"],
        "encoder": inputs["encoder_sha256"],
    }
    assert report["encoder"] == {
        "source_revision": "operator-local-fixture",
        "evidence_kind": "teacher-random",
    }
    assert set(report["limitations"].values()) == {"NOT_RUN"}
    assert set(report["limitations"]) >= {"runtime", "device", "training", "parity", "quality"}
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("seed", True),
        ("seed", -1),
        ("seed", 1.5),
        ("seed", "17"),
        ("device", "gpu"),
        ("device", None),
        ("device", True),
        ("max_seconds", True),
        ("max_seconds", 0),
        ("max_seconds", -1),
        ("max_seconds", float("nan")),
        ("max_seconds", float("inf")),
        ("max_seconds", float("-inf")),
        ("max_seconds", "60"),
        ("max_memory_mib", True),
        ("max_memory_mib", 0),
        ("max_memory_mib", -1),
        ("max_memory_mib", 1.5),
        ("max_memory_mib", float("nan")),
    ],
)
def test_rejects_invalid_requested_settings(
    inputs: dict[str, Any], field: str, value: object
) -> None:
    inputs[field] = value
    with pytest.raises(ValueError, match=field):
        preflight_module().preflight(**inputs)


@pytest.mark.parametrize("name", ["rules", "tfidf", "encoder"])
@pytest.mark.parametrize("failure", ["missing", "wrong-pin", "tampered"])
def test_rejects_unverifiable_inputs(inputs: dict[str, Any], name: str, failure: str) -> None:
    if failure == "missing":
        inputs[name] = inputs[name] / "absent"
    elif failure == "wrong-pin":
        inputs[f"{name}_sha256"] = "0" * 64
    else:
        manifest_name = "encoder-manifest.json" if name == "encoder" else "manifest.json"
        (inputs[name] / manifest_name).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match=r"missing|sha256"):
        preflight_module().preflight(**inputs)


@pytest.mark.parametrize("field", ["dataset_sha256", "split_sha256", "labels"])
def test_rejects_different_encoder_cohort(inputs: dict[str, Any], field: str) -> None:
    root = inputs["encoder"]
    manifest_path = root / "encoder-manifest.json"
    manifest = read_json(manifest_path)
    if field == "labels":
        manifest[field] = list(reversed(manifest[field]))
        config_path = root / "config.json"
        config = read_json(config_path)
        config["id2label"] = dict(enumerate(manifest[field]))
        config_path.write_text(json.dumps(config), encoding="utf-8")
        manifest["files"]["config.json"] = file_sha256(config_path)
    else:
        manifest[field] = "a" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    inputs["encoder_sha256"] = file_sha256(manifest_path)
    with pytest.raises(ValueError, match="cohort identity"):
        preflight_module().preflight(**inputs)


def test_shared_boundary_rejects_method_identity_and_missing_method(inputs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="requires rules and tfidf-linear"):
        verify_comparison_inputs(
            {}, inputs["encoder"], encoder_manifest_sha256=inputs["encoder_sha256"]
        )
    with pytest.raises(ValueError, match="method identity"):
        verify_comparison_inputs(
            {
                "rules": (inputs["tfidf"], inputs["tfidf_sha256"]),
                "tfidf-linear": (inputs["rules"], inputs["rules_sha256"]),
            },
            inputs["encoder"],
            encoder_manifest_sha256=inputs["encoder_sha256"],
        )


def test_preflight_reads_only_and_never_deserializes_or_infers(
    inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    import builtins
    import pickle

    module = preflight_module()
    original_import = builtins.__import__
    original_open = Path.open

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.split(".")[0] in {"torch", "transformers", "safetensors"}:
            pytest.fail("preflight imported model runtime")
        return original_import(name, *args, **kwargs)

    def read_only(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(flag in mode for flag in "wax+"):
            pytest.fail("preflight wrote a file")
        return original_open(path, mode, *args, **kwargs)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("preflight loaded or executed a model")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(Path, "open", read_only)
    monkeypatch.setattr(pickle, "load", forbidden)
    monkeypatch.setattr(pickle, "loads", forbidden)
    for name in ("load_trusted_local_classifier", "predict_documents", "predict_local_encoder"):
        monkeypatch.setattr(
            importlib.import_module("projects.document_intelligence_lab.part_a.protocol"),
            name,
            forbidden,
        )
    assert module.preflight(**inputs)["status"] == "INPUTS_VERIFIED"


def test_unavailable_packages_are_null_without_importing_them(
    inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable(name: str) -> str:
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", unavailable)
    report = preflight_module().preflight(**inputs)
    assert set(report["environment"]["packages"].values()) == {None}
    assert report["environment"]["python"]


def cli_args(inputs: dict[str, Any]) -> list[str]:
    return [
        item for key, value in inputs.items() for item in ("--" + key.replace("_", "-"), str(value))
    ]


@pytest.mark.parametrize("failure", [None, "missing", "wrong-pin", "bad-seed", "bad-budget"])
def test_module_cli_exit_and_json(inputs: dict[str, Any], failure: str | None) -> None:
    if failure == "missing":
        inputs["encoder"] /= "absent"
    elif failure == "wrong-pin":
        inputs["encoder_sha256"] = "0" * 64
    elif failure == "bad-seed":
        inputs["seed"] = "oops"
    elif failure == "bad-budget":
        inputs["max_seconds"] = "nan"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "projects.document_intelligence_lab.part_a.preflight",
            *cli_args(inputs),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == (0 if failure is None else 2)
    assert json.loads(completed.stdout)["status"] == (
        "INPUTS_VERIFIED" if failure is None else "BLOCKED_INPUTS"
    )
    assert completed.stderr == ""


def test_cli_does_not_hide_programmer_errors(
    inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = preflight_module()

    def broken(**kwargs: Any) -> Any:
        raise RuntimeError("programmer bug")

    monkeypatch.setattr(module, "preflight", broken)
    with pytest.raises(RuntimeError, match="programmer bug"):
        module.main(cli_args(inputs))


def test_cli_does_not_hide_unexpected_metadata_value_errors(
    inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(name: str) -> str:
        raise ValueError("metadata programmer bug")

    monkeypatch.setattr(metadata, "version", broken)
    with pytest.raises(ValueError, match="metadata programmer bug"):
        preflight_module().main(cli_args(inputs))


def test_cli_missing_required_flag_is_blocked_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert preflight_module().main([]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED_INPUTS"


@pytest.mark.parametrize("evidence_kind", [[], {}])
def test_cli_blocks_correctly_pinned_malformed_encoder_evidence_kind(
    inputs: dict[str, Any], evidence_kind: object
) -> None:
    manifest_path = inputs["encoder"] / "encoder-manifest.json"
    manifest = read_json(manifest_path)
    manifest["evidence_kind"] = evidence_kind
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    inputs["encoder_sha256"] = file_sha256(manifest_path)

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "projects.document_intelligence_lab.part_a.preflight",
            *cli_args(inputs),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    blocked = json.loads(completed.stdout)
    assert blocked["status"] == "BLOCKED_INPUTS"
    assert "evidence_kind" in blocked["error"]
    assert completed.stderr == ""
    with pytest.raises(ValueError, match="evidence_kind"):
        preflight_module().preflight(**inputs)
