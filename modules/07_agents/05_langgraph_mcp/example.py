"""Use real LangGraph and an in-process MCP SDK client/server, entirely offline."""

import asyncio
from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from mcp import Client
from mcp.server import MCPServer
from mcp.types import TextContent


class GraphState(TypedDict):
    topic: str
    label: str


def normalize_topic(state: GraphState) -> dict[str, str]:
    return {"topic": state["topic"].strip().casefold()}


def prepare_label(state: GraphState) -> dict[str, str]:
    return {"label": f"Catalog request: {state['topic']}"}


def run_graph(topic: str) -> str:
    with tracing_context(enabled=False):
        builder = StateGraph(GraphState)
        builder.add_node("normalize", normalize_topic)
        builder.add_node("label", prepare_label)
        builder.add_edge(START, "normalize")
        builder.add_edge("normalize", "label")
        builder.add_edge("label", END)
        result = builder.compile().invoke({"topic": topic, "label": ""})
    label = result["label"]
    if not isinstance(label, str):
        raise TypeError("graph returned a non-string label")
    return label


@dataclass(frozen=True)
class MCPDemo:
    tool_names: tuple[str, ...]
    required_arguments: tuple[str, ...]
    tools_advertised: bool
    protocol_version: str
    text: str


async def inspect_local_mcp() -> MCPDemo:
    server: MCPServer[None] = MCPServer("Local Museum", log_level="ERROR")

    @server.tool()
    def lookup_exhibit(exhibit_id: str) -> str:
        """Read one entry from the example's in-memory exhibit catalogue."""
        return {"E-001": "Brass telescope"}[exhibit_id]

    # Passing the server object uses SDK in-process transport: no port or subprocess.
    async with Client(server) as client:
        listing = await client.list_tools()
        required = listing.tools[0].input_schema.get("required", [])
        if not isinstance(required, list):
            raise TypeError("tool schema required field must be an array")
        result = await client.call_tool("lookup_exhibit", {"exhibit_id": "E-001"})
        if result.is_error:
            raise RuntimeError("local MCP tool failed")
        return MCPDemo(
            tuple(tool.name for tool in listing.tools),
            tuple(value for value in required if isinstance(value, str)),
            client.server_capabilities.tools is not None,
            client.protocol_version,
            "".join(block.text for block in result.content if isinstance(block, TextContent)),
        )


def main() -> None:
    print(run_graph("  Astronomy  "))
    result = asyncio.run(inspect_local_mcp())
    print(f"MCP tools: {result.tool_names}; required: {result.required_arguments}")
    print(f"Capability advertised: {result.tools_advertised}; result: {result.text}")
    print("Local graph and in-process protocol calls only; no model or external service.")


if __name__ == "__main__":
    main()
