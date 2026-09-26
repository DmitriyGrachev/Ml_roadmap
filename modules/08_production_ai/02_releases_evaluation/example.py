"""Identify frozen evaluation inputs without implementing a release gate."""

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ReleaseManifest:
    model_version: str
    prompt_version: str
    index_version: str
    scorer_version: str
    dataset_sha256: str


def evaluation_manifest(development: frozenset[str], holdout: frozenset[str]) -> ReleaseManifest:
    if not holdout or development & holdout:
        raise ValueError("holdout must be nonempty and disjoint from development")
    encoded = json.dumps(sorted(holdout), ensure_ascii=False, separators=(",", ":")).encode()
    return ReleaseManifest(
        "local-model-v2",
        "museum-v3",
        "catalog-v1",
        "rubric-v2",
        hashlib.sha256(encoded).hexdigest(),
    )


def main() -> None:
    manifest = evaluation_manifest(frozenset({"dev-1"}), frozenset({"holdout-2", "holdout-1"}))
    print(json.dumps(asdict(manifest), sort_keys=True))
    print(
        "This fingerprints fixture case IDs only; real provenance includes complete case content."
    )


if __name__ == "__main__":
    main()
