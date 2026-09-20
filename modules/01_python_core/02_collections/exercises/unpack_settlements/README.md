# Unpack settlement records safely

## Goal

Validate and unpack a three-field settlement row into typed values.

## Difficulty

Beginner

## Estimated time

20–30 minutes

## Edit

Edit only `modules/01_python_core/02_collections/exercises/unpack_settlements/starter.py`.

## Requirements

- Require exactly three fields: transaction ID, decimal amount text, and currency.
- Require transaction ID and currency to be nonblank strings.
- Parse the amount directly with `Decimal`; never convert through `float`.
- Raise `ValueError` for a wrong field count or invalid amount text.

## Acceptance criteria

Valid rows return `tuple[str, Decimal, str]`, every invalid contract case remains visible, and the tests pass.

## Run

`uv run pytest modules/01_python_core/02_collections/exercises/unpack_settlements -q -rx`

## Hints (optional)

Sequence unpacking names the three fields; `Decimal` reports invalid numeric text explicitly.
