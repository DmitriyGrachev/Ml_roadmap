# Plan library record retention

Difficulty: Medium. Estimated time: 35–60 minutes.

Prerequisites: aware datetimes, `timedelta`, stable sorting, immutable records, and
[05 — Privacy](../../05_privacy_security/README.md).

A library service needs a reviewable list of expired records. Apply an explicit age policy
and legal holds to caller-supplied metadata. This exercise only returns candidate IDs;
it never deletes files, updates a database, schedules deletion, or decides legal obligations.

## Contract

Implement `plan_retention(records, now, retention_days)`.

1. `retention_days` is an integer excluding booleans, in `[1, 36500]`. A day means exactly
   24 elapsed hours. `now` and every `created_at` must be timezone-aware datetimes
   (`utcoffset()` is not `None`). Compare absolute instants, using UTC for cutoff arithmetic.
2. Record IDs have 1–80 characters, with no leading/trailing whitespace, and are unique.
   IDs are case-sensitive. `legal_hold` must be a boolean, not an integer surrogate.
   Creation times cannot be later than `now`, including on held records.
3. Validate all records before selecting candidates. Invalid input raises `ValueError`.
   A cutoff that would fall outside the representable datetime range also raises
   `ValueError`. Other inputs use their declared types; error message wording is not prescribed.
4. The cutoff is the UTC instant `now - retention_days * 24 hours`. A record is eligible
   only when `created_at` is **strictly earlier** than that cutoff and `legal_hold` is false.
   Equality stays retained. Held records remain protected regardless of age.
5. Return eligible IDs as a tuple, oldest creation instant first, breaking ties by ID
   lexicographically. Empty input returns `()`. Do not mutate records or use wall-clock time;
   repeated calls with equal inputs return equal candidate lists.

## Example

At `2026-06-20 12:00 UTC` with ten-day retention, the cutoff is `2026-06-10 12:00 UTC`.
An unheld record created one microsecond before it is a candidate. A record at the cutoff
or a much older record under legal hold is not.

## TODO boundary and run

Implement `plan_retention`, including validation, cutoff selection, and deterministic order.

```powershell
uv run pytest modules/08_production_ai/exercises/retention_policy -q -rx
```

Optional hints: normalize aware instants for arithmetic, keep equality separate from
expiration, and validate held records before applying their protection.

Done when the focused tests pass with zero xfails and you can explain why a candidate list
is not deletion authorization: real execution must recheck holds, concurrent changes,
backups, and the applicable policy at the storage boundary.
