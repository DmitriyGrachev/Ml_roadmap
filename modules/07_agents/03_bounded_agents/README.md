# Bounded agents

## Goal

Build a finite model/tool loop whose stop conditions and audit trail are application policy,
even when the model keeps requesting work.

## Java mental model

Think of a worker loop around an untrusted strategy object. The strategy proposes; the
worker validates, enforces budgets, dispatches, records observations, and decides when to stop.

## Python model

Represent decisions as typed alternatives such as `CallTool` and `Finish`. Inject the
model and tool boundary so tests can feed exact proposals and errors. Return a structured
terminal status rather than disguising budget exhaustion as a completed answer.

## Key concepts

Count model turns and tool attempts separately. One model turn can propose an action that
the application refuses to execute. Check a tool budget before the call; count a failed
tool attempt as consumed work. A model declaring `Finish` ends this loop but does not prove
the answer is correct—evaluation remains independent.

Use several limits in production: model turns, tool calls, elapsed time, cost, output size,
and fan-out. A count limit cannot interrupt a hung operation; a pre-step deadline check
cannot cancel a tool already running. Transport timeouts and cooperative cancellation
must exist at their own boundaries. LangGraph's [recursion limit](https://docs.langchain.com/oss/python/langgraph/graph-api#recursion-limit)
is a framework guard, not a replacement for your application's distinct budgets.

Classify expected tool failures and define a bounded recovery policy. Do not catch every
exception and ask the model to improvise: that can hide programming bugs and repeatedly
spend resources. Module 05 covers retry mechanics; here the focus is loop termination and
state. Tool observations remain untrusted data, including text that asks to remove limits.

## Example

```powershell
uv run python modules/07_agents/03_bounded_agents/example.py
```

A deterministic pre-step check compares counters and an injected elapsed-time measurement.
It illustrates a deadline boundary without sleeping or introducing a complete agent loop.

## Exercises

Complete [Bounded exhibit assistant](exercises/bounded_loop/README.md). This Medium task
adds model proposals, one preauthorized read tool, full observation history, exact trace
ordering, and distinct success, limit, and classified-failure terminal states.

## Self-check

1. Why are model turns and tool calls separate counters?
2. Does a failed tool attempt consume budget?
3. Why should budget exhaustion return a distinct status?
4. What can a pre-step deadline check fail to stop?
5. Why must a tool's instruction-like output remain an observation?

## Done when

You can prove the loop cannot exceed its declared counts, identify its remaining timeout
limitations, and reconstruct every tool attempt and terminal decision from its trace.
