# Review a stateful report builder

## Difficulty

Intermediate

## Estimated time

30–45 minutes

## Observed smell

`ReportBuilder.build` produces the correct report, but it stores temporary merchant order and
totals on the instance, resets them before work, and clears them again afterward. Local computation
is expressed as object lifecycle state, making repeated-call reasoning needlessly difficult.

## Reproduce

Run exactly:

`uv run pytest modules/01_python_core/03_functions/code_review/stateful_report -q`

The characterization suite passes before refactoring and must remain green throughout the review.

## Allowed edit

Edit only `modules/01_python_core/03_functions/code_review/stateful_report/review_me.py`.

## Behavior that must remain

- Keep `ReportBuilder.build(rows)` as the public entry point.
- Return immutable merchant totals in first-seen merchant order.
- Sum amounts with exact `Decimal` arithmetic.
- Return an empty report for empty input.
- Reuse one builder safely without prior calls leaking into later reports.
- Do not mutate the input collection or any row inside it.

## Hints (optional)

Separate values that describe a builder from values needed only during one `build` call. A useful
review question is whether another method or caller needs each stored attribute after the call.

## Acceptance criteria

The characterization suite remains green after resettable cross-call instance state is removed.
Ordering, exact totals, empty behavior, repeated-call isolation, and the public API are unchanged.

## Self-review checklist

- [ ] Is temporary report state scoped to one call?
- [ ] Does repeated use of one builder remain independent?
- [ ] Are ordering and exact `Decimal` totals unchanged?
- [ ] Did I preserve input rows and keep all characterization tests green?
