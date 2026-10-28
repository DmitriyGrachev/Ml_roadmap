"""Offline archive-equipment teacher trace using existing module 06 contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from typing import Any

from roadmap_tools.experiment_evidence import checked_artifact

rag = import_module("modules.06_rag.walkthrough")
FIXTURES = Path(__file__).with_name("fixtures")


@dataclass(frozen=True)
class Draft:
    text: str
    citation_ids: tuple[str, ...]


@dataclass(frozen=True)
class Answer(Draft):
    status: str
    grounding_status: str = "REQUIRES_REVIEW"


class ProviderUnavailable(RuntimeError):
    """A provider adapter maps its bounded timeout/outage to this exception."""


type Generator = Callable[[str, tuple[Any, ...]], Draft]


def teacher_sources() -> tuple[Any, ...]:
    """Privileged author listing; never expose this complete corpus to a user."""
    corpus = json.loads((FIXTURES / "corpus.json").read_text(encoding="utf-8"))
    return tuple(rag.Source(**row) for row in corpus["sources"])


def extractive_generator(query: str, passages: tuple[Any, ...]) -> Draft:
    """Deterministic excerpt, NOT an LLM or a semantic answer oracle."""
    return Draft("Source excerpt: " + passages[0].text, (passages[0].chunk_id,))


def _validate_sources(sources: tuple[Any, ...]) -> None:
    if not isinstance(sources, tuple) or any(
        not isinstance(source, rag.Source)
        or any(
            not isinstance(getattr(source, field), str)
            for field in ("source_id", "revision", "access", "raw_text")
        )
        for source in sources
    ):
        raise ValueError("source snapshot must contain typed Source records")
    ids = [source.source_id for source in sources]
    if len(set(ids)) != len(ids):
        raise ValueError("source IDs must be unique")
    if len(sources) > 100 or any(
        not source.source_id.strip()
        or not source.revision.strip()
        or source.access not in {"public", "staff"}
        or not source.raw_text.strip()
        or len(source.raw_text) > 10000
        for source in sources
    ):
        raise ValueError("invalid or unbounded source snapshot")


def answer_query(
    query: str,
    sources: tuple[Any, ...],
    allowed_access: tuple[str, ...] = ("public",),
    *,
    k: int = 2,
    current_sources: tuple[Any, ...] | None = None,
    generator: Generator = extractive_generator,
    character_budget: int = 2000,
) -> Answer:
    """Authorize before top-k; recheck live metadata before calling the provider.

    Actor access comes from trusted caller configuration, never request JSON.
    Callables must bound their own runtime; this synchronous function cannot
    interrupt an arbitrary provider. It does not infer semantic answer support.
    """
    if type(k) is not int or not 1 <= k <= 10:
        raise ValueError("k must be an integer in 1..10")
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise ValueError("query must be nonblank and at most 1000 characters")
    if type(character_budget) is not int or not 0 <= character_budget <= 10000:
        raise ValueError("character_budget must be an integer in 0..10000")
    if any(role not in {"public", "staff"} for role in allowed_access):
        raise ValueError("unsupported trusted access role")
    _validate_sources(sources)
    current = sources if current_sources is None else current_sources
    _validate_sources(current)
    candidates = rag.retrieve(query, sources, allowed_access, k)
    context = rag.assemble_context(
        candidates,
        {source.source_id: source for source in current},
        allowed_access,
        character_budget,
    )
    if not context.passages:
        return Answer("", (), "no_answer")
    try:
        draft = generator(query, context.passages)
    except ProviderUnavailable:
        return Answer("", (), "provider_error")
    valid_ids = {passage.chunk_id for passage in context.passages}
    if (
        not isinstance(draft, Draft)
        or not isinstance(draft.text, str)
        or not draft.text.strip()
        or len(draft.text) > 6000
        or not isinstance(draft.citation_ids, tuple)
        or not draft.citation_ids
        or not all(isinstance(item, str) for item in draft.citation_ids)
        or len(set(draft.citation_ids)) != len(draft.citation_ids)
        or not set(draft.citation_ids).issubset(valid_ids)
    ):
        return Answer("", (), "invalid_output")
    return Answer(draft.text, draft.citation_ids, "answer")


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def run_demo(output: Path) -> dict[str, Any]:
    """Save separate computed retrieval and answer traces in a new author folder."""
    sources = teacher_sources()
    judgments = json.loads((FIXTURES / "queries.json").read_text(encoding="utf-8"))
    retrieval: dict[str, Any] = {}
    answers: dict[str, Any] = {}
    for row in judgments["queries"]:
        candidates = rag.retrieve(row["text"], sources, ("public",), k=2)
        ranked = [candidate.chunk_id for candidate in candidates]
        relevant = set(row["relevant_chunk_ids"])
        ranks = [index for index, chunk_id in enumerate(ranked, 1) if chunk_id in relevant]
        retrieval[row["query_id"]] = {
            "candidates": [asdict(candidate) for candidate in candidates],
            "recall_at_k": len(set(ranked) & relevant) / len(relevant) if relevant else None,
            "reciprocal_rank": 1 / min(ranks) if ranks else (0.0 if relevant else None),
            "answerable_by_annotation": row["answerable"],
        }
        answers[row["query_id"]] = asdict(answer_query(row["text"], sources))
    output.mkdir(parents=True, exist_ok=False)
    _write_json(output / "retrieval.json", retrieval)
    _write_json(output / "answers.json", answers)
    # Copy exact reference bytes: normalization belongs to the index configuration.
    for name in ("corpus.json", "queries.json"):
        (output / name).write_bytes((FIXTURES / name).read_bytes())
    manifest = {
        "schema_version": 1,
        "evidence_kind": "AUTHOR_LEXICAL_AND_EXTRACTIVE_ONLY",
        "config": {
            "normalization": rag.NORMALIZATION,
            "chunking": rag.CHUNK_POLICY,
            "retrieval": "TF-IDF lowercase=True norm=l2 sklearn defaults otherwise",
            "score_semantics": "cosine, not answer correctness probability",
            "generator": "explicit deterministic extractive callable, NOT an LLM",
            "k": 2,
            "allowed_access": ["public"],
            "character_budget": 2000,
        },
        "versions": {"scikit-learn": version("scikit-learn")},
        "code_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path(str(rag.__file__)))
        },
        "artifacts": {
            name: {
                "path": name,
                "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
                "size_bytes": (output / name).stat().st_size,
            }
            for name in ("corpus.json", "queries.json", "retrieval.json", "answers.json")
        },
        "pretrained_quality": "NOT_RUN",
        "qdrant_runtime": "NOT_RUN",
        "answer_quality": "REQUIRES_REVIEW",
        "timing_and_cost": "NOT_MEASURED",
    }
    _write_json(output / "manifest.json", manifest)
    return {"retrieval": retrieval, "answers": answers, **manifest}


def verify_trace(root: Path) -> dict[str, Any]:
    """Byte integrity only; does not authenticate manifests or assess quality."""
    manifest: dict[str, Any] = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
    ):
        raise ValueError("unsupported trace schema")
    for name in ("corpus.json", "queries.json", "retrieval.json", "answers.json"):
        _checked_entry(root, manifest.get("artifacts"), name)
    return manifest


def _checked_entry(root: Path, artifacts: Any, name: str) -> Path:
    if not isinstance(artifacts, dict) or not isinstance(artifacts.get(name), dict):
        raise ValueError("artifact entry must be an object")
    spec = artifacts[name]
    if (
        spec.get("path") != name
        or type(spec.get("size_bytes")) is not int
        or spec["size_bytes"] < 0
    ):
        raise ValueError("artifact path or size differs")
    path = checked_artifact(root, spec["path"], spec.get("sha256"))
    if path.stat().st_size != spec["size_bytes"]:
        raise ValueError("artifact size differs")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run_demo(args.output)
    print(json.dumps({"evidence": result["evidence_kind"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
