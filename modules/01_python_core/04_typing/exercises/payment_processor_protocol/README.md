# Delegate through a payment-processor protocol

## Goal

Use a structural protocol to authorize a payment without coupling the function to a provider class hierarchy.

## Difficulty

Intermediate

## Estimated time

20–35 minutes

## Edit

Edit only `modules/01_python_core/04_typing/exercises/payment_processor_protocol/starter.py`.

## Requirements

- Keep `Payment` and `Authorization` as frozen records with the declared field types.
- Accept any object whose `authorize(payment)` method matches `PaymentProcessor`; explicit inheritance is not required.
- Call `processor.authorize` exactly once with the same `Payment` object.
- Return the exact `Authorization` object supplied by the processor.
- Let a processor-owned domain exception propagate unchanged.

## Acceptance criteria

A class that never names `PaymentProcessor` satisfies the structural boundary, successful delegation happens once, and provider failures keep their original type and identity.

## Run

`uv run pytest modules/01_python_core/04_typing/exercises/payment_processor_protocol -q -rx`

## Hints (optional)

Unlike a Java interface, a Python `Protocol` is satisfied structurally: the compatible method shape matters, not an `implements` declaration.
