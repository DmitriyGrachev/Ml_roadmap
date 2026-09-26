"""A local evidence envelope keeps source identity separate from source text."""

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Passage:
    chunk_id: str
    source_id: str
    revision: str
    text: str


def evidence_envelope() -> dict[str, object]:
    passage = Passage(
        "library-north:r3:0", "library-north", "r3", "North library opens at 09:00 on weekdays."
    )
    return {
        "query_id": "hours-001",
        "corpus_snapshot": "library-fixture-v3",
        "content_role": "untrusted_reference_data",
        "evidence": [asdict(passage)],
    }


def main() -> None:
    print(json.dumps(evidence_envelope(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
