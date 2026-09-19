# 06 — SQLAlchemy 2.x models and sessions

## Goal

Persist typed domain records with SQLAlchemy 2.x while treating a session as a bounded unit of work.

## Java mental model

| Spring | Python and FastAPI |
| --- | --- |
| JPA entity fields map a record. | `Mapped[...]` and `mapped_column` map an ORM model. |
| `EntityManager` manages persistence context. | `Session` manages a unit of work. |

**Non-equivalence:** SQLAlchemy is explicit about statements and session lifetime; it is not JPA with renamed annotations.

## Python model

Use `select()` and typed mappings. Commit a successful unit of work, roll back failures, and close every session through a context manager or request dependency.

## Key concepts

- declarative base
- `Mapped` columns
- `select()` statements
- commit, rollback, close

## Example

A support-ticket repository would receive a `Session`, add one record, and return a response model rather than leaking its ORM entity.

## Exercises

The transaction-repository exercise uses temporary SQLite for behavior that does not require PostgreSQL dialect semantics.

## Self-check

1. What does a session own?
2. When must a session roll back?
3. Why use `select()`?
4. Which value type represents money?
5. Why close sessions on errors too?

## Done when

You can trace a request from a session boundary through commit or rollback and closure.
