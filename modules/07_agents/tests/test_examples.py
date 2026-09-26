"""Check local state transitions and real offline framework boundaries."""

import asyncio
import importlib
from types import ModuleType

import pytest
from langsmith import tracing_context
from langsmith.utils import tracing_is_enabled
from pydantic import ValidationError

LESSONS = (
    "01_workflows_state",
    "02_tools_permissions",
    "03_bounded_agents",
    "04_checkpoints_approvals",
    "05_langgraph_mcp",
    "06_evaluation_handoffs",
)


def load_example(lesson: str) -> ModuleType:
    return importlib.import_module(f"modules.07_agents.{lesson}.example")


@pytest.mark.parametrize("lesson", LESSONS)
def test_examples_run_deterministically(lesson: str, capsys: pytest.CaptureFixture[str]) -> None:
    example = load_example(lesson)
    assert example.main() is None
    output = capsys.readouterr().out
    assert output
    assert example.main() is None
    assert capsys.readouterr().out == output


def test_workflow_enforces_legal_transitions_without_mutation() -> None:
    example = load_example("01_workflows_state")
    original = example.WorkflowState("intake", "  Stars  ")
    reviewed = example.advance(original, "validate")
    assert reviewed == example.WorkflowState("review", "Stars")
    assert example.advance(reviewed, "approve").stage == "ready"
    assert original.title == "  Stars  "
    with pytest.raises(ValueError, match="transition"):
        example.advance(original, "approve")
    with pytest.raises(ValueError, match="title"):
        example.advance(example.WorkflowState("intake", " "), "validate")


def test_tool_visibility_depends_on_application_permissions() -> None:
    example = load_example("02_tools_permissions")
    assert example.visible_tools(frozenset({"catalog:read"})) == ("lookup_exhibit",)
    assert example.visible_tools(frozenset()) == ()
    assert example.visible_tools(frozenset({"catalog:read", "workshops:reserve"})) == (
        "lookup_exhibit",
        "reserve_workshop",
    )


def test_step_start_checks_deadline_and_turn_limit() -> None:
    example = load_example("03_bounded_agents")
    assert example.stop_reason(2, 3, 99, 100) is None
    assert example.stop_reason(3, 3, 99, 100) == "turn_limit"
    assert example.stop_reason(2, 3, 100, 100) == "deadline"


def test_approval_digest_binds_workflow_version_tool_and_arguments() -> None:
    example = load_example("04_checkpoints_approvals")
    digest = example.approval_digest("flow-1", 2, "reserve", {"room": "A", "slot": "10"})
    assert digest == example.approval_digest("flow-1", 2, "reserve", {"slot": "10", "room": "A"})
    assert digest != example.approval_digest("flow-1", 2, "reserve", {"room": "B", "slot": "10"})
    assert digest != example.approval_digest("flow-1", 3, "reserve", {"room": "A", "slot": "10"})
    assert digest != example.approval_digest("flow-2", 2, "reserve", {"room": "A", "slot": "10"})
    assert digest != example.approval_digest("flow-1", 2, "delete", {"room": "A", "slot": "10"})


def test_real_langgraph_runs_nodes_and_keeps_ambient_tracing_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    example = load_example("05_langgraph_mcp")
    original = example.normalize_topic
    observed: list[bool] = []

    def inspect_node(state: dict[str, object]) -> object:
        observed.append(tracing_is_enabled() is not False)
        return original(state)

    monkeypatch.setattr(example, "normalize_topic", inspect_node)
    with tracing_context(enabled=True):
        result = example.run_graph("  Astronomy  ")
    assert result == "Catalog request: astronomy"
    assert observed == [False]


def test_real_in_process_mcp_discovers_capability_schema_and_calls_local_tool() -> None:
    example = load_example("05_langgraph_mcp")
    result = asyncio.run(example.inspect_local_mcp())
    assert result.tool_names == ("lookup_exhibit",)
    assert result.tools_advertised
    assert result.required_arguments == ("exhibit_id",)
    assert result.text == "Brass telescope"
    assert result.protocol_version


def test_handoff_requires_goal_and_rejects_claimed_authority() -> None:
    example = load_example("06_evaluation_handoffs")
    handoff = example.Handoff.model_validate(
        {"goal": "Date the telescope", "facts": ["Brass body"], "open_questions": ["Maker?"]}
    )
    assert handoff.open_questions == ["Maker?"]
    for payload in (
        {"goal": "", "facts": [], "open_questions": []},
        {"goal": "Date it", "facts": [], "open_questions": [], "admin": True},
    ):
        with pytest.raises(ValidationError):
            example.Handoff.model_validate(payload)
