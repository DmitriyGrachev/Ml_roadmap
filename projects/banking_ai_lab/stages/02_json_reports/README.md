# Stage 02 — analytics and JSON reports

## Prerequisites

Complete Stage 01 plus the iterators/generators and exceptions/I/O lessons. Review frozen
dataclasses, one-shot iterables, exact `Decimal` arithmetic, UTF-8 JSON, and atomic file replacement.

## Goal

Build a deterministic immutable transaction report and export it without exposing a partially
written destination.

## Estimated time

75–90 minutes

## Edit

Edit only `build_report` and `write_report_json` in
`projects/banking_ai_lab/banking_ai_lab/analytics.py`.

## Report schema

`TransactionReport` contains transaction and fraud counts, optional UTC period bounds, ordered
currency summaries, ordered status summaries, and at most three merchant summaries. Currency and
merchant summaries contain `transaction_count` and `total_amount`; status summaries contain
`transaction_count`. Public collections are tuples.

## Requirements

- Traverse a transaction iterable once, preserve `Decimal`, and do not mutate caller-owned input.
- Order currencies and statuses alphabetically.
- Order at most three merchants by descending total amount, then merchant name.
- Serialize decimals as strings and aware timestamps as UTC ISO 8601 strings.
- Write UTF-8 JSON through a sibling temporary file and atomic replacement.
- On serialization or replacement failure, preserve any destination, remove only the owned
  temporary file, and propagate the original exception.
- Reject a missing parent directory rather than creating it.

## Acceptance criteria

Every report component, neutral empty input, one-shot input, deterministic Unicode JSON, missing
parents, successful replacement, and both failure-cleanup paths pass independently.

## Run

`uv run pytest projects/banking_ai_lab/tests/test_analytics.py -q -rx`

## Hints (optional)

Keep aggregation state separate from the frozen output records. A temporary path must be a sibling
of the destination for replacement to stay on the same filesystem; cleanup belongs in a failure-safe
scope.

## Completion checklist

- [ ] Every report component and ordering rule passes.
- [ ] One-shot and empty inputs pass without float conversion.
- [ ] JSON bytes are deterministic and retain Unicode.
- [ ] Both failure paths preserve the target and unrelated neighboring files.
