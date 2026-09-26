# Prompt contracts

## Goal

Turn an underspecified text request into a versioned task contract with explicit evidence,
output expectations, and behavior when evidence is missing.

## Java mental model

A prompt template resembles a versioned request builder, not a magic string constant.
Separate application-owned policy from caller text, as you would separate a query's
structure from its values. The analogy has limits: quoting data does not make an LLM
immune to malicious instructions within that data.

## Python model

Store trusted instructions separately; serialize source strings with `json.dumps` instead
of manually escaping quotes. Give documents stable identifiers so an answer can name its
sources. A model adapter maps this application structure to supported provider roles.

## Key concepts

A useful contract specifies the task, audience, allowed evidence, output format, and
abstention behavior. For a library assistant: answer only from supplied references; cite
reference IDs; say that the references do not establish an answer when necessary. A worked
example can clarify the format, but should not leak held-out evaluation answers.

Version the template and evaluate revisions against the same cases. Change one material
variable at a time so improvements can be attributed. Avoid inserting secrets or granting
tools merely because a prompt asks the model to behave.

Documents and tool results can contain indirect prompt injections. Preserve their origin
and keep their text out of the trusted instruction channel. JSON encoding preserves string
boundaries; it cannot guarantee semantic obedience. Permission checks and output validation
must remain in application code. See the provider's [prompt-injection guidance](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks)
for its specific content channels; our exercise message schema is provider-neutral.

## Example

```powershell
uv run python modules/05_llm_engineering/02_prompt_contracts/example.py
```

The translation contract specifies a fallback and a worked format example. An instruction-like
source string stays inside a JSON value. This demonstrates representation, not model safety.

## Exercises

Implement [Library reference messages](exercises/prompt_messages/README.md), a Medium task
covering role construction, validation, exact source preservation, and adversarial strings.

## Self-check

1. What would happen if a document were concatenated into the system instruction?
2. What does JSON quoting guarantee, and what does it leave unresolved?
3. Why must examples and held-out cases be kept separate?

## Done when

You can state the prompt's contract, identify each input's trust level, and pass the message
exercise without changing source data or promoting its text into an instruction role.
