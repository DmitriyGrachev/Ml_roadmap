"""Worked author geometry: directions hand-written, no LLM/pretrained quality claim."""

import json

from . import runtime as rt


def main() -> None:
    vectors = [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [-1.0, 0.0]]
    rows = []
    for case in rt.teacher_cases():
        query = [-1.0, 0.0] if case["kind"] == "missing" else [1.0, 0.0]
        rows.append(
            rt.run_case(
                case,
                rt.teacher_chunks(),
                vectors,
                query,
                rt.Config(k=1),
                rt.demo.extractive_generator,
            )
        )
    print(
        json.dumps(
            {
                "evidence_kind": "AUTHOR_HAND_GEOMETRY_EXTRACTIVE_ONLY",
                "pretrained_quality": "NOT_RUN",
                "llm_quality": "NOT_RUN",
                "interpretation": "REQUIRES_REVIEW",
                "cases": rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
