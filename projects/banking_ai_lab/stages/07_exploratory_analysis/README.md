# Stage 07 — exploratory transaction analysis

## Prerequisites

Complete [Stage 06](../06_testing/README.md), then review Pandas inspection, aware UTC timestamps,
descriptive statistics, grouped summaries, and why rare-class evaluation needs more than accuracy.

## Time box

Plan 45–90 minutes, including a final reset and self-check.

## Editable surface

Edit only cells tagged `exercise` in
`projects/banking_ai_lab/notebooks/transaction_eda.ipynb`. The setup, typed loading, inspection, and
safe aggregate-count cells are complete infrastructure. Keep the checked-in synthetic dataset at
`datasets/transactions.csv`; do not substitute real financial records.

## Run the contracts

From the repository root, start JupyterLab (or open the same file with PyCharm's notebook support):

```powershell
uv run jupyter lab projects/banking_ai_lab/notebooks/transaction_eda.ipynb
```

Run the focused notebook contract from the repository root:

```powershell
uv run pytest projects/banking_ai_lab/tests/test_notebook.py -q
```

For Colab, upload `transaction_eda.ipynb`, run its setup cell, and upload the checked-in synthetic
`transactions.csv` when prompted. The fallback needs no network download. Work through only the
tagged exercise cells, then clear every output before downloading the notebook.

## Acceptance criteria

- The stored notebook remains nbformat v4 with Python 3 metadata and no saved outputs.
- Setup uses the fixed seed and repository-relative dataset path and works from the repository root.
- Decimal text crosses the documented Stage 3 analysis boundary into `float64`, timestamps become
  aware UTC values, and inspection exposes only schema, dtype, shape, and aggregate-count
  information.
- All six exercise cells remain independently unfinished until you complete their requested
  missing-value, duplicate, distribution, aggregation, temporal, and fraud-metric analyses.
- The notebook contains no local absolute path, credential, network dependency, or real customer
  data.

## Hints

Complete one tagged cell at a time and rerun the focused contract after each change. Preserve the
original `transactions` frame when an analysis needs sorting or transformation. Keep UTC explicit
and explain why a rare positive class makes accuracy alone misleading.

## Reset and cleanup

Use **Restart Kernel and Clear All Outputs** in PyCharm/Jupyter or Colab before saving. To discard
all notebook work and return to the starter, restore
`projects/banking_ai_lab/notebooks/transaction_eda.ipynb` from Git. Do not commit Colab checkpoints
or uploaded datasets.

## Completion checklist

- [ ] Every tagged exercise runs without the starter `NotImplementedError`.
- [ ] Results are deterministic under `RANDOM_SEED = 20260919`.
- [ ] Amount, timestamp, missing-value, duplicate, aggregation, temporal, and fraud checks are
      explained in your own words.
- [ ] All outputs and execution counts are cleared before commit.
- [ ] The focused notebook contract and complete project suite pass.
