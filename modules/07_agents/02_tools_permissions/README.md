# Tools and permissions

Разбор schema, прав и exact approval: [теория 02](theory.md).

## Goal

Treat a model-proposed tool call as untrusted input and let application code decide whether
the exact operation may run.

## Java mental model

A tool dispatcher resembles an allowlisted command bus: deserialize a known command type,
validate its fields, authorize it for the authenticated caller, and invoke the registered
handler. The command itself cannot supply its own permissions.

## Python model

Use a trusted registry, strict Pydantic argument models, and a separate permission set
derived by the application. An executor receives validated arguments rather than raw
model text. Discovery can hide unavailable tools, but dispatch must recheck permissions.

## Key concepts

Tool names, descriptions, and input schemas help a model propose valid work. They do not
grant authority. Deny unknown names, unexpected fields, coerced identifiers, and actions
outside the caller's scope. In a real application, authorization may also bind a tenant,
resource, operation, and current resource version; a tool-name allowlist is only this
exercise's deliberately small policy.

Treat tool output as data with provenance. Text returned by a tool may contain prompt
injection, so it cannot rewrite the registry, budgets, or permissions. A label saying
`readOnly` is descriptive metadata, not proof of safety. The MCP [tools specification](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
describes tool discovery and invocation; the host still controls which proposed operations
it authorizes.

Never resolve a function through `eval`, `exec`, shell commands, or a dynamic import chosen
by model text. Use explicit application-owned functions. Keep side effects separate from
read operations and add approval where application policy requires it. Record the call ID,
operation, decision, and result without treating full sensitive payload logging as mandatory.

## Example

```powershell
uv run python modules/07_agents/02_tools_permissions/example.py
```

A trusted catalogue exposes only the lookup tool to a caller with catalog-read permission.
Filtering descriptions is an aid to proposal generation, not the final execution gate.

## Exercises

Implement [Authorized museum tool dispatch](exercises/tool_dispatch/README.md), a Medium
task that selects argument schemas, denies unauthorized execution, and preserves tool output
without interpreting it as instructions. Executors in the tests are local recorders.

## Self-check

1. Why is a discovered tool not an authorized tool?
2. Where should the permission set come from?
3. How can tool output contain untrusted instructions?
4. Why is a model-supplied `approved` field not approval?
5. Which checks must still occur after discovery filtering?

## Done when

Invalid and unauthorized proposals cannot reach an executor, while permitted calls receive
typed arguments and produce an auditable result through an explicit registry.
