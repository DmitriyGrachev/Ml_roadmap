"""Read-only local input verification; no model execution or learner credit.

INPUTS_VERIFIED means inventory/cohort integrity only. It does not establish
runnable model bytes, provenance authenticity, a trained classifier, resource
feasibility, or learner credit. Requested settings are not execution evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
from collections.abc import Sequence
from importlib import metadata
from pathlib import Path
from typing import Any, NoReturn

from .protocol import verify_comparison_inputs


class InputError(ValueError):
    """Expected invalid operator input, distinct from unexpected runtime failures."""


class _InputParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise InputError(message)


def preflight(
    *,
    rules: Path,
    rules_sha256: str,
    tfidf: Path,
    tfidf_sha256: str,
    encoder: Path,
    encoder_sha256: str,
    seed: int,
    device: str,
    max_seconds: float,
    max_memory_mib: int,
) -> dict[str, Any]:
    """Verify externally pinned inputs and report requested, unexercised settings."""
    if type(seed) is not int or seed < 0:
        raise InputError("seed must be a nonnegative integer")
    if device not in ("cpu", "cuda"):
        raise InputError("device must be cpu or cuda")
    if type(max_seconds) not in (int, float) or not math.isfinite(max_seconds) or max_seconds <= 0:
        raise InputError("max_seconds must be positive and finite")
    if type(max_memory_mib) is not int or max_memory_mib <= 0:
        raise InputError("max_memory_mib must be a positive integer")
    try:
        bundles, manifest = verify_comparison_inputs(
            {"rules": (rules, rules_sha256), "tfidf-linear": (tfidf, tfidf_sha256)},
            encoder,
            encoder_manifest_sha256=encoder_sha256,
        )
    except (ValueError, OSError) as exc:
        raise InputError(str(exc)) from exc
    reference = bundles["rules"]
    packages: dict[str, str | None] = {}
    for package in ("numpy", "scipy", "scikit-learn", "torch", "transformers", "safetensors"):
        try:
            packages[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            packages[package] = None
    return {
        "status": "INPUTS_VERIFIED",
        "execution": "NOT_RUN",
        "quality": "NOT_EVALUATED",
        "requested_settings": {
            "seed": seed,
            "device": device,
            "max_seconds": max_seconds,
            "max_memory_mib": max_memory_mib,
        },
        "dataset_sha256": reference.manifest["dataset_sha256"],
        "split_sha256": reference.manifest["split_sha256"],
        "labels": list(reference.dataset.labels),
        "evaluation_ids": list(reference.splits["test"]),
        "manifest_pins": {
            "rules": rules_sha256,
            "tfidf-linear": tfidf_sha256,
            "encoder": encoder_sha256,
        },
        "encoder": {
            "source_revision": manifest["source_revision"],
            "evidence_kind": manifest["evidence_kind"],
        },
        "environment": {"python": platform.python_version(), "packages": packages},
        "limitations": {
            name: "NOT_RUN"
            for name in (
                "runtime",
                "device",
                "training",
                "parity",
                "quality",
                "resource_feasibility",
            )
        },
        "scope": (
            "Inventory/cohort integrity only; runnable model bytes, provenance authenticity, "
            "trained classifier, resource feasibility and learner credit are not established. "
            "Requested settings are not execution evidence."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Print verified inventory or expected input failure as JSON."""
    parser = _InputParser(description=__doc__, allow_abbrev=False)
    for name in ("rules", "tfidf", "encoder"):
        parser.add_argument(f"--{name}", required=True, type=Path)
        parser.add_argument(f"--{name}-sha256", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--max-seconds", required=True)
    parser.add_argument("--max-memory-mib", required=True)
    try:
        args = parser.parse_args(argv)
        try:
            seed = int(args.seed)
            max_seconds = float(args.max_seconds)
            max_memory_mib = int(args.max_memory_mib)
        except ValueError as exc:
            raise InputError(str(exc)) from exc
        report = preflight(
            rules=args.rules,
            rules_sha256=args.rules_sha256,
            tfidf=args.tfidf,
            tfidf_sha256=args.tfidf_sha256,
            encoder=args.encoder,
            encoder_sha256=args.encoder_sha256,
            seed=seed,
            device=args.device,
            max_seconds=max_seconds,
            max_memory_mib=max_memory_mib,
        )
    except InputError as exc:
        print(json.dumps({"status": "BLOCKED_INPUTS", "error": str(exc)}))
        return 2
    print(json.dumps(report, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
