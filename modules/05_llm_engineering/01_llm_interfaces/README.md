# LLM interfaces

## Goal

Define the contract your application needs from a language-model provider without coupling
business logic to a particular SDK or response envelope.

## Java mental model

A `Protocol` plays the role of a small service interface, with structural typing: an object
can satisfy it by exposing the required method without inheriting from it. An adapter maps
external response fields into your own records. See Python's [Protocol documentation](https://docs.python.org/3.12/library/typing.html#typing.Protocol).

## Python model

`CompletionRequest` and `Completion` are immutable records. `LabelClient.complete` is the
boundary. `FixedClient` returns a known response so that `generate_label` can be tested
without credentials, network calls, stochastic generation, or a tokenizer.

## Key concepts

An LLM generates token sequences conditioned on input; it is not a factual database. Your
adapter should distinguish successful completion, truncation, refusal, transport errors,
and invalid output. The example's `stop`, `length`, and `refusal` values are our normalized
application vocabulary, not universal provider field names.

Chat roles and their serialization differ across model families. A provider adapter owns
that translation; [Hugging Face chat templates](https://huggingface.co/docs/transformers/chat_templating)
show why a list of role/content messages eventually becomes model-specific token sequences.
Our fixture usage numbers are illustrative, not measurements.

Put timeouts, authentication, model/version settings, and provider error mapping at the
adapter boundary. Keep business policy outside it. Log request identifiers, version,
duration, and usage without indiscriminately logging source text or secrets. Small sampling
settings can reduce variation; they are not an application-level correctness guarantee.

## Example

```powershell
uv run python modules/05_llm_engineering/01_llm_interfaces/example.py
```

The fake returns a museum label. `generate_label` refuses to publish a response whose
termination reason signals incomplete work. A real provider could return plausible but
false text even with `stop`; later lessons add validation and evaluation.

## Exercises

Trace the request, provider call, normalized response, and application decision. Then complete
the [bounded retry exercise](../06_reliability_and_tools/exercises/bounded_retry/README.md)
after lesson 06 to apply an interface to transient failure handling.

## Self-check

1. What part of the interface changes when you change providers?
2. Why is a fixed fake useful even though it cannot assess answer quality?
3. Why must a truncated label not be treated as an ordinary success?

## Done when

You can replace `FixedClient` with another structurally compatible client and identify
which concerns belong to the adapter, the application, and a live-model evaluation.
