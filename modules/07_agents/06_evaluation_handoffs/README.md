# Evaluation and handoffs

## Goal

Evaluate the path a workflow took and preserve useful context when another worker or a
person must continue the task.

## Java mental model

A trace resembles structured operational events, not just a log line containing the final
response. A handoff resembles a typed work item containing confirmed facts, unresolved
questions, and a clear owner; it does not transfer unrestricted execution privileges.

## Python model

Use explicit per-run and per-call records. Keep expected final correctness separate from
authorization decisions, tool outcomes, limits, and repeated calls. Build a concise handoff
record from state rather than asking a model to reconstruct everything from a long transcript.

## Key concepts

An answer can be correct after an unauthorized action or a budget overrun. Report task
success together with policy violations, terminal reasons, call counts, repeated actions,
tool failures, and latency/cost from Module 05. Define denominators: a policy violation can
be counted per call, while a limit violation may be counted once per run.

Repeated equivalent calls can signal a loop or missing state, but can also represent
intentional retries. Count them as a diagnostic metric, then inspect context; do not label
every repeat a safety violation. A recovered tool failure need not make the entire task
unsuccessful if the final result and policy remain valid.

Golden trace cases should cover direct completion, necessary tools, denied actions,
repeated proposals, exhaustion, failures, and changed approvals. Local scripted traces
verify your scorer and orchestration; they cannot establish how often a real model will
choose a good action. Preserve held-out scenarios for prompt and policy comparisons.

A useful handoff includes the user's goal, verified observations with source references,
unresolved work, current status, and reason for handoff. Keep guesses distinguishable from
facts. The receiving worker needs its own permission and resource checks. Avoid endlessly
bouncing tasks: cap handoffs and assign ownership. Human review should receive enough
context to make a decision, including what is uncertain and what action awaits approval.

## Example

```powershell
uv run python modules/07_agents/06_evaluation_handoffs/example.py
```

A Pydantic record carries an exhibit-identification goal, a catalogue fact, and a question
for an archive reviewer. An extra `admin` field is rejected; a handoff is data, not authority.

## Exercises

Implement [Evaluate workflow traces](exercises/trace_evaluation/README.md), a Medium task
with success criteria, per-call authorization violations, per-run limit violations,
redundancy accounting, and a tool-failure denominator.

## Self-check

1. How can a correct final answer still represent an unsuccessful run?
2. Why must each metric state its denominator?
3. When might repeated calls be legitimate?
4. Which facts and uncertainties belong in a handoff?
5. Why does a receiving worker need fresh permission and budget checks?

## Done when

Your trace metrics expose policy and efficiency failures hidden by final-answer accuracy,
and your handoffs retain useful context without inventing evidence or granting authority.
