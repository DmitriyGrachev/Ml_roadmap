"""Consistency gate for independently produced live evidence; never authorship proof."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MODES = ("base", "improved_prompt", "lora")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checked(root: Path, name: str, expected: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("artifact path must remain inside its root")
    path = root / relative
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("artifact cannot use symlinks")
    if not path.is_file() or sha256(path) != expected:
        raise ValueError(f"missing or changed artifact: {name}")
    return path


def validate_snapshot(snapshot: dict[str, Any], kind: str) -> None:
    """Check all supported tokenizer assets, including separately saved named templates.

    Supported local fast-tokenizer snapshots require tokenizer.json and its config.
    All JSON/Jinja/text/vocabulary/SentencePiece/tiktoken assets under the snapshot
    are identified, not only files a submitter volunteered. Hub local-dir cache
    bookkeeping is not a tokenizer input and is excluded.
    """
    local = Path(snapshot["path"])
    if not local.is_absolute() or not local.is_dir() or not snapshot.get("source_revision"):
        raise ValueError("explicit local snapshot and source revision required")
    names = snapshot["files"]
    if kind == "base_snapshot":
        weights = {p.relative_to(local).as_posix() for p in local.rglob("*.safetensors")}
        if "config.json" not in names or not weights or not weights <= names.keys():
            raise ValueError("base identity requires config and every local safetensors shard")
    elif kind == "tokenizer_snapshot":
        required = {"tokenizer.json", "tokenizer_config.json"}
        suffixes = {".json", ".jinja", ".txt", ".model", ".vocab", ".merges", ".tiktoken", ".bpe"}
        assets = {
            p.relative_to(local).as_posix()
            for p in local.rglob("*")
            if p.is_file() and p.suffix in suffixes and ".cache" not in p.relative_to(local).parts
        }
        if not (required | assets) <= names.keys():
            raise ValueError("all local tokenizer assets and templates must be identified")
    else:
        raise ValueError("unknown snapshot kind")
    for name, digest in names.items():
        checked(local, name, digest)


def json_equal(actual: Any, expected: Any) -> bool:
    """JSON equality with recursive boolean/number separation; 1 and 1.0 normalize."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            json_equal(actual[key], expected[key]) for key in expected
        )
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(
            json_equal(a, b) for a, b in zip(actual, expected, strict=True)
        )
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return bool(actual == expected)
    return type(actual) is type(expected) and bool(actual == expected)


def score(rows: list[dict[str, Any]], predictions: list[dict[str, str]]) -> dict[str, float]:
    """Recompute JSON parse, exact expected fields, and unsupported refusal rates."""
    if any(
        not isinstance(row.get("id"), str)
        or not row["id"]
        or type(row.get("supported")) is not bool
        or not isinstance(row.get("expected"), dict)
        or (not row["supported"] and not json_equal(row["expected"], {"unsupported": True}))
        for row in rows
    ):
        raise ValueError("invalid expected/supported/ID schema")
    wanted = {row["id"]: row for row in rows}
    if len(wanted) != len(rows) or len(predictions) != len(rows):
        raise ValueError("prediction IDs must cover each holdout row exactly once")
    if {p["id"] for p in predictions} != set(wanted):
        raise ValueError("prediction IDs differ from holdout")
    parsed = correct = unsupported = 0
    unsupported_total = sum(not row["supported"] for row in rows)
    if not rows or not unsupported_total or unsupported_total == len(rows):
        raise ValueError("holdout requires supported and unsupported examples")
    for prediction in predictions:
        row = wanted[prediction["id"]]
        try:
            value = json.loads(prediction["text"])
        except (ValueError, TypeError):
            value = None
        valid = isinstance(value, dict)
        parsed += valid
        correct += valid and json_equal(value, row["expected"])
        unsupported += not row["supported"] and json_equal(value, {"unsupported": True})
    return {
        "parse_success": parsed / len(rows),
        "field_correctness": correct / len(rows),
        "unsupported_handling": unsupported / unsupported_total,
    }


def validate_evidence(root: Path) -> str:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("exercise_id") != "lab-sft-lora"
        or manifest.get("origin") != "LEARNER"
        or manifest.get("evidence_kind") != "LIVE_PRETRAINED"
        or manifest.get("review_status") != "REQUIRES_REVIEW"
    ):
        raise ValueError("requires independent LEARNER LIVE_PRETRAINED evidence")
    if not manifest.get("domain") or not manifest.get("authorship_explanation"):
        raise ValueError("new domain and authorship explanation are required")
    artifacts = manifest["artifacts"]
    required = (
        "dataset.json",
        "splits.json",
        "predictions.json",
        "runner.py",
        "adapter/adapter_model.safetensors",
        "adapter/adapter_config.json",
    )
    paths = {name: checked(root, name, artifacts[name]) for name in required}
    if not paths["runner.py"].read_text(encoding="utf-8").strip():
        raise ValueError("independently written runner is required")
    for kind in ("base_snapshot", "tokenizer_snapshot"):
        validate_snapshot(manifest[kind], kind)
    rows = json.loads(paths["dataset.json"].read_text(encoding="utf-8"))
    split = json.loads(paths["splits.json"].read_text(encoding="utf-8"))
    if set(split) != {"train", "validation", "holdout"} or any(not ids for ids in split.values()):
        raise ValueError("three nonempty splits required")
    ids = [row["id"] for row in rows]
    all_split = [identifier for part in split.values() for identifier in part]
    if (
        len(set(ids)) != len(ids)
        or len(set(all_split)) != len(all_split)
        or set(ids) != set(all_split)
    ):
        raise ValueError("split IDs must partition the dataset")
    families: dict[str, str] = {}
    for part, identifiers in split.items():
        for row in rows:
            if row["id"] in identifiers:
                if not row.get("family") or families.get(row["family"], part) != part:
                    raise ValueError("paraphrase family crosses splits")
                families[row["family"]] = part
    if set(manifest["trained_ids"]) != set(split["train"]):
        raise ValueError("training IDs must contain train only")
    if any(row["id"].startswith("author-") for row in rows):
        raise ValueError("author fixture is not independent learner data")
    predictions = json.loads(paths["predictions.json"].read_text(encoding="utf-8"))
    if set(predictions) != set(MODES):
        raise ValueError("base/improved_prompt/lora must share the holdout")
    holdout = [row for row in rows if row["id"] in split["holdout"]]
    for mode in MODES:
        if manifest["metrics"][mode] != score(holdout, predictions[mode]):
            raise ValueError("metrics differ from saved prediction arithmetic")
    # A random teacher report or empty placeholder cannot masquerade as an adapter.
    import torch
    from safetensors.torch import load_file

    tensors = load_file(str(paths["adapter/adapter_model.safetensors"]))
    if not tensors or not all(
        "lora_" in key and torch.isfinite(t).all() for key, t in tensors.items()
    ):
        raise ValueError("finite actual LoRA safetensors required")
    return "REQUIRES_REVIEW"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    print(validate_evidence(parser.parse_args().root))


if __name__ == "__main__":
    main()
