"""Offline teacher trace for a fictional bicycle service guide.

Prepared completions illustrate an application contract; no model is called.
"""

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

PUBLIC_GUIDE = "Overnight storage is not offered. Pickup by 19:00."
QUESTION = "Can I leave a bicycle overnight?"
SUCCESS = (
    '{"status":"unavailable","next_step":"none","evidence_id":"G-01",'
    '"evidence_quote":"Overnight storage is not offered."}'
)
UNSUPPORTED = (
    '{"status":"available","next_step":"visit","evidence_id":"G-01",'
    '"evidence_quote":"Pickup by 19:00."}'
)


@dataclass(frozen=True)
class Request:
    question: str
    context_id: str
    context_version: str
    context_access: str
    context: str
    instruction: str


@dataclass(frozen=True)
class Budget:
    limit: int
    framing: int
    instruction: int
    question: int
    context: int
    tools: int
    input_units: int
    reserve: int
    remaining: int


@dataclass(frozen=True)
class Decision:
    stage: str
    safe_next_step: str


class GuideAnswer(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    status: Literal["available", "unavailable", "unknown"]
    next_step: Literal["visit", "none", "contact"]
    evidence_id: str
    evidence_quote: str


def build_request(question: str, permission: str) -> Request | None:
    """Select source before creating a model-facing request."""
    if "access code" in question.lower() and permission != "staff":
        return None
    if "access code" in question.lower():
        return Request(
            question,
            "G-STAFF",
            "2026-09",
            "staff",
            "Staff access code: DEMO-ONLY.",
            "Answer from context.",
        )
    return Request(
        question,
        "G-01",
        "2026-09",
        "public",
        PUBLIC_GUIDE,
        "Answer the overnight-storage question using only the cited guide; abstain if unsupported.",
    )


def account_budget(
    *,
    limit: int,
    framing: int,
    instruction: int,
    question: int,
    context: int,
    tools: int,
    reserve: int,
) -> Budget:
    """Add fictional accounting units, not actual tokenizer tokens."""
    parts = (limit, framing, instruction, question, context, tools, reserve)
    if any(part < 0 for part in parts):
        raise ValueError("budget parts must be nonnegative")
    input_units = framing + instruction + question + context + tools
    if input_units + reserve > limit:
        raise ValueError("budget exceeded")
    return Budget(
        limit,
        framing,
        instruction,
        question,
        context,
        tools,
        input_units,
        reserve,
        limit - input_units - reserve,
    )


def decide_completion(raw: str, finish_reason: str, request: Request) -> Decision:
    """Gate a prepared answer in technical, schema, semantic, then evidence order."""
    if finish_reason == "refusal":
        return Decision("refused", "show_refusal")
    if finish_reason != "stop":
        return Decision("truncated", "request_new_completion")
    if not raw.strip():
        return Decision("empty", "show_unavailable")
    try:
        answer = GuideAnswer.model_validate_json(raw)
    except ValidationError:
        return Decision("schema_failure", "show_unavailable")
    if answer.status == "unavailable" and answer.next_step != "none":
        return Decision("semantic_failure", "show_unavailable")
    if answer.status == "available" and answer.next_step != "visit":
        return Decision("semantic_failure", "show_unavailable")
    if answer.status == "unknown" and answer.next_step != "contact":
        return Decision("semantic_failure", "show_unavailable")
    # This is a deliberately narrow check for one fixed guide and one fixed question.
    if not (
        request.question == QUESTION
        and request.context_id == "G-01"
        and request.context_version == "2026-09"
        and request.context_access == "public"
        and request.context == PUBLIC_GUIDE
        and answer.status == "unavailable"
        and answer.evidence_id == "G-01"
        and answer.evidence_quote == "Overnight storage is not offered."
        and answer.evidence_quote in PUBLIC_GUIDE
    ):
        return Decision("evidence_failure", "show_unavailable")
    return Decision("accepted", "display_answer_only")


def make_trace(
    permission: str, question: str, raw: str = SUCCESS, finish_reason: str = "stop"
) -> dict[str, object]:
    """Show request construction, prepared completion, and application decision."""
    request = build_request(question, permission)
    if request is None:
        return {
            "request": None,
            "completion": None,
            "decision": asdict(Decision("access_denied", "explain_access_limit")),
        }
    return {
        "request": asdict(request),
        "completion": {"prepared_text": raw, "finish_reason": finish_reason},
        "decision": asdict(decide_completion(raw, finish_reason, request)),
    }


def build_demo() -> dict[str, object]:
    """Collect deterministic examples; the figures are fictional accounting."""
    return {
        "disclaimer": (
            "Prepared completions, fictional budget units and rates; "
            "no model, tokenizer or network."
        ),
        "guide": {"id": "G-01", "version": "2026-09", "access": "public", "text": PUBLIC_GUIDE},
        "budget": asdict(
            account_budget(
                limit=100, framing=15, instruction=20, question=10, context=35, tools=0, reserve=20
            )
        ),
        "cases": {
            "success": make_trace("public", QUESTION),
            "unsupported": make_trace("public", QUESTION, UNSUPPORTED),
            "denied": make_trace("visitor", "What is the staff access code?"),
            "refusal": make_trace("public", QUESTION, "", "refusal"),
            "truncated": make_trace("public", QUESTION, '{"status":"unavailable"', "length"),
            "malformed": make_trace("public", QUESTION, "{broken"),
            "empty": make_trace("public", QUESTION, ""),
        },
    }


def save_trace(output: Path) -> Path:
    """Create a fresh directory and refuse even an existing empty one."""
    output.mkdir(parents=True, exist_ok=False)
    trace_path = output / "trace.json"
    trace_path.write_text(
        json.dumps(build_demo(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return trace_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    path = save_trace(args.output)
    print(f"Teacher trace: {path}")
    print("Prepared completions only; no model was called.")


if __name__ == "__main__":
    main()
