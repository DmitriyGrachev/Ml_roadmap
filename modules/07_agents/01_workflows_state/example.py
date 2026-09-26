"""A workflow makes allowed transitions explicit and creates new state snapshots."""

from dataclasses import dataclass, replace
from typing import Literal


@dataclass(frozen=True)
class WorkflowState:
    stage: Literal["intake", "review", "ready"]
    title: str


def advance(state: WorkflowState, event: Literal["validate", "approve"]) -> WorkflowState:
    if state.stage == "intake" and event == "validate":
        if not state.title.strip():
            raise ValueError("title cannot be blank")
        return replace(state, stage="review", title=state.title.strip())
    if state.stage == "review" and event == "approve":
        return replace(state, stage="ready")
    raise ValueError(f"invalid transition: {state.stage} -> {event}")


def main() -> None:
    state = WorkflowState("intake", "  Astronomy collection  ")
    events: tuple[Literal["validate", "approve"], ...] = ("validate", "approve")
    for event in events:
        state = advance(state, event)
        print(state)
    print("Ready is a workflow state; no exhibit was published.")


if __name__ == "__main__":
    main()
