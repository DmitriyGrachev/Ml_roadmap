"""Classify manually reviewed outcomes rather than infer semantic support."""

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewedOutcome:
    answerable: bool
    evidence_retrieved: bool
    supported_answer: bool
    abstained: bool


def failure_counts() -> dict[str, int]:
    reviewed = [
        ReviewedOutcome(True, True, True, False),
        ReviewedOutcome(True, False, False, True),
        ReviewedOutcome(True, True, False, False),
        ReviewedOutcome(False, False, False, True),
    ]
    labels = []
    for row in reviewed:
        if not row.answerable and row.abstained:
            labels.append("correct_abstention")
        elif not row.evidence_retrieved:
            labels.append("retrieval_miss")
        elif not row.supported_answer:
            labels.append("answer_failure")
        else:
            labels.append("supported_answer")
    return dict(sorted(Counter(labels).items()))


def main() -> None:
    print(failure_counts())


if __name__ == "__main__":
    main()
