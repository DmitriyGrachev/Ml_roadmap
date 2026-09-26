# Report library loans

Difficulty: Medium · Estimated time: 40–60 minutes

## Prerequisites

Module 03 Pandas and data-quality lessons: column selection, missing values,
uniqueness, merge cardinality, and DataFrame copies.

## Requirements

Implement `build_loan_report(books, loans)` in `starter.py`.

- `books` requires `book_id` and `title`; `loans` requires `loan_id`, `book_id`,
  and `days`. Extra columns are allowed. Missing required columns or duplicate
  column names in either input raise `ValueError` with `column` in the message.
- Book IDs in `books` and loan IDs in `loans` must be non-null and unique. Loan
  book references must be non-null and refer to a known book. Repeated book
  references in different loans are valid. Raise `ValueError` for bad keys,
  even if a join would otherwise hide or duplicate those rows; include `key` in the message.
- Fixtures use string IDs and titles. Each `days` value must be a nonnegative
  integer (Python or NumPy integer), with no booleans, fractions, missing values,
  infinities, or numeric strings. Raise `ValueError` with `days` in the message for invalid days.
- Produce a new DataFrame with exactly `loan_id`, `title`, `days` in that order,
  one row per loan in original loan order, and a fresh default zero-based index.
  Do not depend on incoming index values, which may be repeated or unsorted.
- Empty loans produce an empty report with the same three columns. Never mutate
  either input or expose their data through a writable result. Output numeric
  dtype is not prescribed.

## Example

```text
books: book_id title       loans: loan_id book_id days
       b2      Clouds            l2      b1      4
       b1      Trees             l1      b2      0

report: loan_id title  days
        l2      Trees  4
        l1      Clouds 0
```

## Edge cases and optional hints

Consider an unknown book, duplicate catalog IDs, several loans of one book, and
an empty loan table. A merge with `validate="many_to_one"` protects cardinality;
an indicator or explicit membership check can expose unmatched references.
Project only the relevant columns before merging to avoid extra-column clashes.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/03_data_foundations/exercises/library_joins -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails and the report
cannot silently multiply or drop loan records because of invalid keys.
