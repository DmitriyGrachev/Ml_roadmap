# Data Foundations notebooks

These notebooks complement the concise lesson READMEs with focused, executable experiments. Open
the repository root in PyCharm and start Jupyter with:

```powershell
uv run jupyter lab
```

Run cells from top to bottom. Each notebook first looks for
`datasets/transactions.csv` relative to the repository root. The dataset is added by the Banking AI
Lab workstream. Until then, the completed examples use a small synthetic fallback. In Google Colab,
the setup cell offers `files.upload()` when the repository dataset is unavailable.

Cells tagged `exercise` belong to you. Their `NotImplementedError` is deliberate: replace the
exception only after writing the requested code. Use **Restart Kernel and Run All** when checking
stateful mistakes, then clear outputs before committing a notebook. No exercise requires network
access or private data.

- `01_numpy_payment_arrays.ipynb` — arrays, masks, broadcasting, axes, and dot products.
- `02_pandas_transaction_analysis.ipynb` — inspection, cleaning, grouping, joins, and datetimes.
- `03_fraud_metrics.ipynb` — confusion-matrix reasoning and imbalanced fraud metrics.
