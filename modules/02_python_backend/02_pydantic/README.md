# 02 — Pydantic request and response models

## Goal

Describe API inputs and outputs with Pydantic 2 models so validation happens at the HTTP boundary.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| Bean Validation annotates a DTO. | Pydantic fields and model validators describe a contract. |
| Jackson serializes a response DTO. | FastAPI serializes a response model. |

**Non-equivalence:** Pydantic validation is model parsing and serialization, not a Java bean-validation layer attached to mutable POJOs.

## Python model

Use `BaseModel`, `Field`, `ConfigDict`, and typed values such as `Decimal` and timezone-aware `datetime`. Declare a response model to avoid returning accidental fields.

## Key concepts

- request versus response schemas
- field constraints and error details
- decimal money values
- forbidden extras and JSON Schema

## Example

`TicketCreate` rejects an empty support subject before `TicketService.create` runs.

## Exercises

The transaction-contract exercise will validate amount, currency, merchant, timestamp, and unexpected fields without persisting a payment.

## Self-check

1. Why use `Decimal` for money?
2. Which layer should reject a blank subject?
3. What does a response model protect?
4. Why reject a naive timestamp?
5. When should extra fields be forbidden?

## Done when

You can distinguish request validation from domain rules and inspect a Pydantic-generated schema.
