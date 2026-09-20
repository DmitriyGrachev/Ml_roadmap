# Test one provider interaction

## Goal

Implement a narrow provider boundary and use the acceptance test to verify one external
interaction without reproducing provider behavior.

## Difficulty

Beginner

## Estimated time

20–30 minutes

## Edit

Edit only `modules/01_python_core/09_testing/exercises/mock_provider/starter.py`.

## Requirements

- Keep the structural `QuoteProvider` protocol.
- Call `provider.quote` exactly once.
- Forward `merchant_id` and `currency` unchanged and in their declared order.
- Return the provider's `Decimal` result exactly; do not convert through `float` or round it.
- Do not catch provider exceptions or introduce retries.

## Acceptance criteria

One focused mock records exactly one expected interaction, while the real function result proves
that the boundary returns the provider's exact decimal value.

## Run

`uv run pytest modules/01_python_core/09_testing/exercises/mock_provider -q -rx`

## Hints (optional)

The protocol is the seam: the implementation should remain a small delegation. Keep assertions
about return behavior and external interaction distinct in your reading of the test.

## Self-check

1. Why is a protocol sufficient for the mock's specification?
2. Which boundary is external to the function under test?
3. How does the test detect a duplicate provider call?
4. Would constructing a new `Decimal` add value here?
5. Where would retry behavior belong instead?
