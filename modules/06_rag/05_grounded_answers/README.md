# Grounded answers and citation checks

## Goal

The [Russian context and citation explanation](theory.md) follows the G-01 passage
through revision checks, a bounded context and a prepared illustrative answer.

Assemble a bounded evidence context and distinguish citation integrity from semantic
support. Define when the application should abstain or request a narrower question.

## Java mental model

Rendering a database foreign key is not the same as verifying a business claim. Likewise,
an existing citation ID and matching quote establish a reference relationship, not
that the quote logically supports the answer or is still factually current.

## Python model

Pass authorized, revision-aware passages as structured data. Keep instructions separate
from source content, reserve space for the question and answer, and retain source IDs
through context trimming. Define an explicit no-evidence path before calling a generator.

## Key concepts

- A production context budget uses the actual model tokenizer and includes all message overhead.
  The example uses characters only and labels that simplifying assumption.
- Avoid duplicate overlapping passages and preserve exceptions or neighboring conditions.
- Treat commands inside retrieved pages as untrusted source text; they cannot authorize tools.
- Check citation IDs, source ownership and exact quotes mechanically. Assess claim support
  separately, with a rubric and reviewed examples; an exact quote can be irrelevant.
- Missing, conflicting or outdated evidence can warrant abstention. A retrieval score
  threshold alone is not calibrated proof that enough evidence exists.

References: [RAG evidence architecture](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview)
and [original retrieval/generation formulation](https://arxiv.org/abs/2005.11401).

## Example

```powershell
uv run python modules/06_rag/05_grounded_answers/example.py
```

Pack preauthorized snippets as JSON under an explicitly artificial character budget.
No evidence yields an abstention state. This is context preparation, not generated text
or a semantic citation verifier.

## Exercises

Complete [Evidence citation validation](exercises/citation_validation/README.md).
Report structural errors and uncited claims while preserving the distinction between
quote integrity and the truth or logical support of a claim.

## Self-check

1. Why can a valid quote still fail to support its attached claim?
2. What must be counted in a real context-token budget?
3. Why should source text never grant tool permissions?
4. What is lost if truncation removes the exception after a rule?
5. When should the answer path abstain even though retrieval returned passages?

## Done when

You can preserve provenance through context assembly, validate reference integrity,
and explain which answer-quality questions still require semantic evaluation.
