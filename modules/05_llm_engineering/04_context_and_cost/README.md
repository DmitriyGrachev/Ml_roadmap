# Context and cost

## Goal

Fit useful evidence inside a known request budget while retaining output capacity and
making cost assumptions visible.

## Java mental model

A context budget is a resource limit, similar to a bounded message payload. Reserve capacity
before filling it. Never confuse a convenient local size proxy with the remote service's
actual accounting units.

## Python model

Inject a `Callable[[str], int]` counter into packing logic. Use `Decimal` values built from
strings for supplied monetary rates; Python documents why [decimal arithmetic](https://docs.python.org/3.12/library/decimal.html)
avoids binary float representation surprises for decimal fractions.

## Key concepts

Tokens are model/tokenizer-specific units, not universally characters or words. Count the
final serialized request, including role framing, instruction, tool schemas, and source
metadata. [Chat templates](https://huggingface.co/docs/transformers/chat_templating) can add
special tokens, so summing separately tokenized strings is not always the final count.

For this module's simplified budget, require `input_budget + reserved_output <= context_limit`.
Real adapters also check any separate input/output limits and provider-specific accounting.
Leave margin when counts are estimates. Silent [truncation](https://huggingface.co/docs/transformers/main/pad_truncation)
can discard critical evidence; choose a documented policy such as keeping whole excerpts in
priority order and reporting omissions. The exercise implements that policy, not retrieval.

For one uncached text request, estimated cost is
`(input_tokens * input_rate + output_tokens * output_rate) / 1_000_000`, where both supplied
rates are per million tokens in the same currency. Do not round each component prematurely.
Actual bills may distinguish cached input, other modalities, or additional usage categories;
retries also accumulate usage. Read the chosen provider's current pricing before live work.
This module publishes no real prices.

## Example

```powershell
uv run python modules/05_llm_engineering/04_context_and_cost/example.py
```

At invented rates of 2 and 8 units per million, 1,200 input and 300 output tokens cost 0.0048
units. That is an arithmetic fixture, not a provider quote.

## Exercises

Complete [Nature-guide context budget](exercises/context_budget/README.md), a Medium packing
task with a caller-supplied counter, whole-document selection, and explicit dropped IDs.

## Self-check

1. Why is `len(text)` unsuitable as a billed token count?
2. What can be lost when a document is cut halfway through?
3. How do failed requests and retries alter a cost estimate?

## Done when

You can account for every term in a context budget, explain the limits of additive estimates,
and compute exact supplied-rate decimal estimates without presenting fixtures as real prices.
