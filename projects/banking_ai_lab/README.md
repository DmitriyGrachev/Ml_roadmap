# Banking AI Lab

Build one synthetic banking project in seven stages. Each stage keeps its student-owned functions
unfinished until you implement them and run its focused tests from the repository root.

| Stage | Outcome | Status |
| --- | --- | --- |
| [01](stages/01_csv_validation/README.md) | Validate transaction CSV rows | Ready |
| [02](stages/02_json_reports/README.md) | Build analytics and atomic JSON reports | Ready |
| [03](stages/03_pandas_analysis/README.md) | Analyze transactions with Pandas | Ready |
| 04 | Expose selected operations through FastAPI | Planned |
| 05 | Persist transactions with PostgreSQL and SQLAlchemy | Planned |
| 06 | Add API and database integration tests | Planned |
| 07 | Explore transaction and fraud patterns in a notebook | Planned |

## Working rules

- Run commands from the repository root so the shared locked environment is used.
- Edit only the functions named by the current stage; domain and result records are infrastructure.
- Keep money as `Decimal` until Stage 3 explicitly crosses into a floating-point DataFrame view.
- Preserve aware UTC timestamps and deterministic ordering at every boundary.

## Synthetic data and privacy

The checked-in datasets are deterministic and wholly synthetic. They contain synthetic user IDs,
not names, emails, account numbers, card numbers, or identifiers derived from real customers. Never
replace them with production or personal financial data.

Run all currently available project tests with:

`uv run pytest projects/banking_ai_lab -q -rx`
