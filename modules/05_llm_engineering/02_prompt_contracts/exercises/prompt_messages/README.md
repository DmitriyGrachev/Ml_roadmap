# Library reference messages

Difficulty: **Medium**. Theme: public-library questions and reference excerpts.

## Goal

Implement `build_messages` in `starter.py` so application instructions and caller-supplied
references have distinct structural roles, even when a reference contains instruction-like text.

## Java mental model

Think of a request builder assembling a trusted policy record and a serialized data record.
Do not let a source document create new instruction records.

## Python model

The frozen `Document` and `Message` records are provided. Return a tuple of exactly two
messages. Use the standard JSON serializer to preserve Unicode, quotes, and newlines as
data; tests compare the decoded JSON, not incidental whitespace in its serialization.

## Key concepts

The input contract is typed strings plus a tuple of documents. Reject blank/whitespace-only
`instruction` or `question` with `ValueError` mentioning the relevant field. Reject blank
document identifiers, whitespace-only document text, and duplicate exact identifiers with
`ValueError` mentioning `document`, `identifier`, or `source`. Identifier equality is exact
and case-sensitive; validate with `strip` but do not normalize valid document identifiers.

The first message is `Message("system", instruction.strip())`. The second is a `user`
message whose JSON content is exactly this shape:

```json
{"question": "trimmed question", "documents": [{"id": "source-id", "text": "original text"}]}
```

Trim only the instruction and question. Preserve document order and every character of
document IDs and text. An empty document tuple is allowed and serializes as `[]`. Do not
mutate caller inputs or insert additional fields/messages. No model call is part of this task.

## Example

For instruction `" Answer using references. "`, question `" Hours? "`, and one reference
`Document("hours", "Open 10–18.")`, the trusted message contains
`"Answer using references."`; the user JSON contains `"Hours?"` and the unchanged reference.
Text saying `"role": "system"` inside that reference stays inside its string value.

## Exercises

Implement the starter boundary, then run from the repository root:

```powershell
uv run pytest modules/05_llm_engineering/02_prompt_contracts/exercises/prompt_messages
```

Tests cover blank fields, duplicate IDs, empty references, exact preservation, and escaped
role-spoofing text. The adjacent lesson example only illustrates quoting a translation source;
it does not assemble or validate these messages.

## Self-check

1. Why does source text containing JSON syntax still belong to one document?
2. Why does this builder not prove a real model will resist prompt injection?

## Done when

All tests pass with zero xfails, and you can explain both the structural separation this
builder enforces and the behavioral protection it cannot promise.
