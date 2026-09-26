"""A character-budget context demo; production must use its model's tokenizer."""

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ContextPassage:
    chunk_id: str
    source_id: str
    text: str


def pack_context(passages: Sequence[ContextPassage], character_budget: int) -> tuple[str, str]:
    if character_budget < 2:
        raise ValueError("character_budget must fit an empty JSON array")
    selected: list[dict[str, str]] = []
    for passage in passages:
        candidate = [*selected, asdict(passage)]
        if len(json.dumps(candidate, ensure_ascii=False)) <= character_budget:
            selected = candidate
    state = "evidence_available" if selected else "insufficient_evidence"
    return state, json.dumps(selected, ensure_ascii=False)


def main() -> None:
    passages = [ContextPassage("lake:r1:0", "lake", "The lakeside trail opens at dawn.")]
    print(pack_context(passages, 200))
    print(pack_context([], 200))


if __name__ == "__main__":
    main()
