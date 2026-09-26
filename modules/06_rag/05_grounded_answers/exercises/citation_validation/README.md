# Evidence citation validation

Difficulty: Medium

Estimated time: 45–60 minutes. Prerequisites: frozen records, mappings and grounded-answer lesson.

A library assistant returns structured citations. Check that each reference identifies
an available chunk from the claimed source and quotes an exact substring. The application
has already authorized the evidence and frozen its revision. This exercise does **not**
determine whether a quote supports the claim, whether the source is true, or whether
permissions changed later.

## Contract

Implement `validate_citations` returning the supplied `CitationReport`.

- Claim IDs are unique nonblank strings. Evidence chunk IDs are unique nonblank strings;
  source IDs are nonblank strings. Preserve spelling and order. Empty evidence text is
  permitted. Invalid claim/evidence metadata raises `ValueError` mentioning `claim` or
  `evidence`, even when there are no citations. Empty input sequences are valid.
- Citation fields are strings. Classify each citation using the **first** matching
  condition below; emit one `CitationIssue` with its zero-based input index.

  | Precedence | Condition | Code |
  | --- | --- | --- |
  | 1 | claim ID is not declared | `unknown_claim` |
  | 2 | chunk ID is not in supplied evidence | `unknown_chunk` |
  | 3 | source ID differs from that chunk's source | `source_mismatch` |
  | 4 | quote is empty or whitespace only | `empty_quote` |
  | 5 | quote is not an exact substring of that chunk | `quote_not_found` |
  | 6 | identical citation was already accepted | `duplicate_citation` |

- Exact substring means case-sensitive, whitespace-sensitive Unicode matching; do not
  strip, normalize or search other chunks as a fallback. A quote existing in another
  source is insufficient. A nonblank substring containing outer spaces is allowed.
- Return accepted citations in original order in `valid`; return issues in original
  order. Duplicates compare all four fields. Distinct quotes for the same claim/chunk
  are allowed. Invalid citations do not mark a claim as cited.
- `uncited_claims` includes declared claims without any accepted citation, in declaration
  order. Do not mutate inputs. No network, model calls or source loading belongs here.

## Edge cases

Unknown claims/chunks, a forged source ID, a quote copied from another chunk, case and
whitespace differences, duplicate citations, several valid quotes per claim, and no evidence.

## Run

```powershell
uv run pytest modules/06_rag/05_grounded_answers/exercises/citation_validation -q
```

Done when every citation has a deterministic structural outcome and your explanation
clearly separates quote integrity from semantic support and current authorization.
