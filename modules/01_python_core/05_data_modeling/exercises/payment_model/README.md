# Model an immutable payment

## Goal

Complete a frozen dataclass that rejects invalid payment values when it is constructed.

## Difficulty

Beginner

## Estimated time

20–30 minutes

## Edit

Edit only `modules/01_python_core/05_data_modeling/exercises/payment_model/starter.py`.

## Requirements

- Keep `Payment` as a frozen dataclass with the existing field names and types.
- Require a nonblank `identifier`.
- Require a finite `Decimal` amount strictly greater than zero.
- Require exactly three uppercase ASCII letters for `currency`.
- Raise `ValueError` naming the invalid field; do not normalize invalid input silently.

## Acceptance criteria

Valid values construct an immutable payment, and every invariant fails independently with
`ValueError`.

## Run

`uv run pytest modules/01_python_core/05_data_modeling/exercises/payment_model -q -rx`

## Hints (optional)

A frozen dataclass may validate initialized fields in `__post_init__`. `Decimal` exposes a finite
value check, and string predicates can express the currency format without a regular expression.

## Self-check

1. Why is `Decimal("NaN")` not a positive payment amount?
2. Does frozen prevent mutation after construction?
3. Why should validation reject rather than uppercase a currency?
4. Which exception type communicates a value-object invariant failure?
5. Are the identifier and currency checks whitespace-aware?
