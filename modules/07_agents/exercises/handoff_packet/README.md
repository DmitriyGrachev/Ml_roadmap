# Prepare a permission-filtered library handoff

Difficulty: Medium. Estimated time: 45–70 minutes.

Prerequisites: immutable records, tuple iteration, string slicing, and
[06 — Evaluation and handoffs](../../06_evaluation_handoffs/README.md).

A library assistant escalates a catalog question to another worker. Build the exact context
the recipient is allowed to see while retaining the case identifier and handoff reason.
The caller supplies those required metadata fields already approved for this recipient.

## Contract

Implement `build_handoff(case_id, reason, facts, recipient_capabilities, max_chars)`.
Inputs use the declared types; implement validation inside this function.

1. `case_id` has 1–80 characters and `reason` has 1–160. Fact names and capability names
   have 1–40 characters. These fields cannot have leading or trailing whitespace.
   All fact names are unique, including names on facts the recipient cannot read.
   Fact values may be empty and may contain arbitrary text. Names are case-sensitive.
2. `max_chars` is an integer excluding booleans, in `[1, 4096]`. It bounds the sum of the
   character counts of the packet's `case_id`, `reason`, and every included fact name and
   value. Count Python string characters, not encoded bytes or serialized JSON punctuation.
   If required metadata alone exceeds the budget, raise `ValueError`.
3. Validate **all** fact structure before filtering. Invalid inputs raise `ValueError`,
   including malformed hidden facts. Message wording is not prescribed.
4. Retain only facts whose capability appears in the trusted `recipient_capabilities`.
   Hidden facts use no budget, are never copied into the output, and cannot by themselves
   set `truncated=True`. Do not include permission names, hidden-fact counts, or placeholders.
5. Consume permitted facts in input order after reserving space for both metadata fields.
   Include complete facts while they fit. At the first fact that does not fit, include its
   name and the longest prefix of its value that fits **if the complete name fits**.
   A zero-length value prefix is allowed. If its name does not fit, omit that fact.
   In either case set `truncated=True` and stop; never skip ahead to a smaller later fact.
6. If every permitted fact fits, return `truncated=False`, including when no facts are
   permitted. An exactly fitting final fact is not truncated. Return a `HandoffPacket`
   with `VisibleFact` records, preserve inputs, and make the result deterministic.

## Example

For case `"C"`, reason `"R"`, and permitted facts `("a", "abc")`, `("b", "xyz")`,
`max_chars=8` leaves six characters for facts. Return the complete `("a", "abc")`, then
`("b", "x")`, and `truncated=True`. A preceding forbidden fact does not change this result.

## TODO boundary and run

Implement `build_handoff`; the starter supplies data shapes only.

```powershell
uv run pytest modules/07_agents/exercises/handoff_packet -q -rx
```

Optional hints: separate validation, permission filtering, and budgeting. Write down which
fields consume the budget before handling the first partial value.

Done when the focused tests pass with zero xfails and you can explain that permission labels
are application policy: this function does not discover secrets embedded in otherwise
permitted text, sanitize prompt injection, or provide a serialized transport-byte limit.
