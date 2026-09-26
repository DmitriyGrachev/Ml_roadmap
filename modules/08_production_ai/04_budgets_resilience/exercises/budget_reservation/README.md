# Track a request budget ledger

Difficulty: Medium. Estimated time: 60–90 minutes.

Prerequisites: Decimal arithmetic, dictionaries, state transitions, and lesson 04.
Replay a supplied sequence of museum-label request events into a deterministic budget report.
This local replay verifies historical accounting. It does not authorize live calls, lock a
shared balance, reserve provider capacity, or prevent concurrent processes from overspending.

## Contract

Implement `summarize_budget(limit, events)` in `starter.py`:

- `limit` and every event amount must be finite `Decimal` values between 0 and
  1,000,000 inclusive and exact multiples of `Decimal("0.01")`. Numeric
  strings/floats are invalid; `Decimal("0.100")` is valid because it equals 0.10.
  Validate the limit even for an empty event sequence. Errors mention `limit` or `amount`.
  This two-decimal quantum is an exercise policy; real per-token costs may need finer units.
- Request IDs are nonblank strings, preserved exactly. Kinds are exactly `reserve`,
  `settle`, or `cancel`. Invalid IDs/kinds raise `ValueError` naming `request` or `kind`.
- Process events in order. A first `reserve` needs a strictly positive amount;
  a nonpositive amount raises `ValueError` mentioning `amount`. The amount must
  fit `available = limit - spent - held`, with equality allowed. Insufficient
  available budget raises `ValueError` mentioning `budget`. A valid reserve creates
  a pending reservation and holds its amount.
- Replaying a reserve with the **same ID and original amount** is a no-op in any
  state, including settled/cancelled. It must not reopen a terminal reservation.
  A changed reserve amount for that ID raises `ValueError` mentioning `amount` or `reserve`.
- `settle` requires an existing pending request, with `0 <= actual <= reserved`.
  Release its entire hold, add actual cost to spent, and retain original reserved amount
  plus actual cost in a settled record. Thus unused reserved capacity becomes available.
- An identical settle replay on an already settled request is a no-op. A different
  actual amount, or settlement of a cancelled request, is invalid.
- `cancel` requires amount zero and an existing pending request. Release its hold;
  retain a cancelled record with `actual=None`. Repeated cancellation is a no-op.
  Cancelling a settled request is invalid. Settling/cancelling an unknown ID is invalid.
  Invalid transitions raise `ValueError` mentioning `request`, `amount`, `reserve`,
  `settle`, `cancel`, or `terminal`.
- Enforce the budget at **every event**, not just the final state. A later refund
  cannot repair an earlier overspend. Return no partial report after any invalid event.
- Return `BudgetReport` with native Decimal totals and reservations sorted by ID.
  Maintain `limit == spent + held + available`; all totals are nonnegative. Pending
  and cancelled records have `actual=None`. Empty events yield zero spent/held and full
  availability. Repeated calls agree; do not mutate inputs or make external calls.

## Example

At limit 10, reserve 4 for `a`, reserve 3 for `b`, settle `a` at 2.50, then cancel `b`.
The result has spent 2.50, held 0, available 7.50. Replaying any identical event leaves
the terminal result unchanged; reserving `a` for 5 is a conflicting replay.

## TODO boundary and run

Implement `summarize_budget`. Dataclasses are supplied, while validation, state transitions,
idempotency, and balance calculations are intentionally unsolved.

```powershell
uv run pytest modules/08_production_ai/04_budgets_resilience/exercises/budget_reservation -q -rx
```

Completion means zero xfails and an explanation of why a live shared reservation service
would need atomic operations, durable idempotency, reconciliation, and bounded retention.
