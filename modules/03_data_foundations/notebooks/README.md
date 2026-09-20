# Data Foundations notebooks

These notebooks complement the concise lesson READMEs with focused, executable experiments. Open
the repository root in PyCharm and start Jupyter with:

```powershell
uv run jupyter lab
```

Run cells from top to bottom. Each notebook first looks for
`datasets/transactions.csv` relative to the repository root. The dataset is added by the Banking AI
Lab workstream. Until then, completed examples use small synthetic data from domains that are
different from the student exercises. No network access is required.

For Google Colab, follow this workflow in order:

1. In Google Colab, choose **File → Upload notebook** and open the required `.ipynb` file.
2. Run the code cell tagged `setup` before any completed example or exercise.
3. Choose `transactions.csv` when the upload prompt appears; cancel only to use synthetic examples.
4. Run the completed examples, then replace each deliberate exception and run every exercise.
5. Clear all outputs, then use **File → Download → Download .ipynb** to save your work.

Cells tagged `exercise` belong to you. Their `NotImplementedError` is deliberate: replace the
exception only after writing the requested code. Use **Restart Kernel and Run All** when checking
stateful mistakes, then clear outputs before committing a notebook. Do not put credentials or
personal customer fields in a notebook.

- `01_numpy_payment_arrays.ipynb` — arrays, masks, broadcasting, axes, and dot products.
- `02_pandas_transaction_analysis.ipynb` — inspection, cleaning, grouping, joins, and datetimes.
- `03_fraud_metrics.ipynb` — confusion-matrix reasoning and imbalanced fraud metrics.
