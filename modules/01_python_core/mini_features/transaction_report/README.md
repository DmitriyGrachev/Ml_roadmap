# Build a transaction analytics report

## Goal

Build one immutable report from a stream of transaction rows while preserving exact monetary values
and deterministic output.

## Exercise type

Type E — mini-feature

## Difficulty

Intermediate

## Estimated time

60–90 minutes

## Edit

Edit only `modules/01_python_core/mini_features/transaction_report/report.py`.

## Input schema

Each `TransactionRow` has these fields:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | `str` | Required and nonblank |
| `amount` | `Decimal` | Required, finite, and not negative |
| `currency` | `str` | Required; exactly three uppercase ASCII letters |
| `status` | `str` | Required and nonblank |
| `merchant` | `str` | Required and nonblank |
| `metadata` | `dict[str, str]` | Optional; accepted but not aggregated |

No other fields are accepted. A malformed row raises `ValueError` whose message identifies it as a
transaction-row error. Do not skip or partially aggregate invalid rows.

## Report schema

`TransactionReport` is frozen and contains:

- `transaction_count`: number of input rows;
- `total_amount`: sum of all amounts as `Decimal`;
- `totals_by_currency`: `CurrencyTotal` records ordered by currency;
- `counts_by_status`: `StatusCount` records ordered by status;
- `top_merchants`: at most three `MerchantTotal` records.

Merchant records are ordered by descending total amount and then ascending merchant name. Currency
and status records use ascending alphabetical order. An empty input produces zero, `Decimal("0")`,
and empty tuples.

## Requirements

- Accept any iterable, including a one-shot generator, and traverse it exactly once.
- Aggregate repeated currencies, statuses, and merchants.
- Keep every amount as `Decimal`; do not convert through `float`.
- Do not mutate the iterable, its rows, or nested metadata.
- Apply the invalid-row policy before returning a report.
- Keep the supplied frozen output records and public function signature.

## Acceptance criteria

The complete acceptance suite passes for mixed currencies, repeated merchants, tied totals,
one-shot input, empty input, exact decimal arithmetic, deep non-mutation, and malformed rows.

## Run

`uv run pytest modules/01_python_core/mini_features/transaction_report -q -rx`

## Hints (optional)

One loop can update several independent accumulators. `dict` is suitable for aggregation, while
`sorted` with a tuple key makes a tie-break rule explicit. Validate a row before adding any of its
values to the accumulators.

## Review questions

1. Where does the implementation prove that the input is traversed only once?
2. Which operation guarantees that no binary floating-point value enters an amount?
3. What neutral values does the empty report use?
4. How are repeated merchants combined?
5. Which sort key implements the merchant tie-break?
6. Why are currency and status totals represented as tuples of frozen records?
7. At what point is a row validated relative to aggregation?
8. What happens if invalid data appears after several valid rows?
9. Can any code path mutate `metadata` or a caller-owned row?
10. Which acceptance test would fail if a fourth merchant leaked into the report?
