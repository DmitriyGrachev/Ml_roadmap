# LangGraph and MCP

## Goal

Use a real local workflow graph and a real in-process tool protocol connection while
understanding the different responsibility each technology serves.

## Java mental model

LangGraph resembles an execution/state-machine framework. MCP resembles a protocol and
typed client/server boundary for discovering and invoking capabilities. A workflow may
use an MCP tool inside a node, but the protocol does not decide the workflow's policy.

## Python model

The example uses the repository's locked LangGraph 1.2 and MCP SDK 2.2 APIs. `StateGraph`
receives a `TypedDict` state schema, nodes return updates, edges define order, and `compile`
produces a runnable graph. Separately, `Client(server)` connects to an `MCPServer` object
using the SDK's in-process transport. This is an actual protocol client/server interaction,
not a hand-written JSON object presented as MCP.

## Key concepts

| Concern | LangGraph | MCP |
| --- | --- | --- |
| Ordering and state | Nodes, edges, updates, checkpoints | Carries requests/results across a boundary |
| Tool exposure | Application chooses a node's callable | Server advertises tools and input schemas |
| Execution authority | Application policy around nodes | Host/server authorization around calls |
| Completion | Graph stop conditions | A protocol result does not complete the user's larger goal |

The [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) supports state
updates, branching, and reducers; this example is a two-node fixed workflow with no model.
Graph execution uses [tracing_context(enabled=False)](https://docs.langchain.com/langsmith/trace-without-env-vars)
to keep the example local even if tracing is enabled in the surrounding environment.

The [MCP SDK client lifecycle](https://py.sdk.modelcontextprotocol.io/client/) is an async
context: enter, discover capabilities, list tools, call an allowed tool, then close. The
current SDK probes current servers and supports older handshakes. For protocol
2025-11-25, the [classic lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
uses `initialize` to negotiate version/capabilities, followed by `notifications/initialized`
before normal operations. Do not assume that exact handshake for every future protocol
version; the locked SDK negotiates its supported version.

Tool discovery exposes names and schemas, not user permission. Validate inputs and results,
handle tool errors, and treat returned text as untrusted. The example's one tool reads a
hardcoded public catalogue; there is no account access, port, subprocess, credential, or
external mutation. Production transports and authentication require additional policy.

## Example

```powershell
uv run python modules/07_agents/05_langgraph_mcp/example.py
```

The graph normalizes a topic and prepares a label. The MCP client checks the tool capability,
reads the tool's required argument schema, and calls the local exhibit lookup. It then closes
the connection through the async context manager.

## Exercises

Trace both paths in the example. Connect what you learned to the Medium
[tool dispatcher](../02_tools_permissions/exercises/tool_dispatch/README.md) and
[bounded loop](../03_bounded_agents/exercises/bounded_loop/README.md): identify where
application checks would surround a graph node or MCP call. No hosted integration is needed.

## Self-check

1. Which component decides the next workflow step?
2. What does a server's tools capability advertise?
3. How does discovery differ from authorization?
4. Why must protocol lifecycle explanations name the relevant version?
5. What does this in-process example verify, and what would a deployed transport add?

## Done when

The actual graph and in-process protocol example run locally, and you can assign state,
discovery, transport, permissions, and stopping rules to the correct application boundaries.
