"""Score a frozen set of library questions, including required refusals."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Case:
    identifier: str
    expected_answer: str | None


@dataclass(frozen=True)
class Prediction:
    identifier: str
    answer: str | None
    latency_ms: float
    cost: Decimal


@dataclass(frozen=True)
class Evaluation:
    total: int
    correct: int
    accuracy: float
    answer_accuracy: float | None
    refusal_accuracy: float | None
    mean_latency_ms: float
    p95_latency_ms: float
    total_cost: Decimal


def evaluate_answers(cases: tuple[Case, ...], predictions: tuple[Prediction, ...]) -> Evaluation:
    """Join by ID, validate records, and compute metrics defined in README.md."""
    raise NotImplementedError("Implement the offline library-answer evaluator")
