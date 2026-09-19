# Module 03 Data Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build practical NumPy, Pandas, statistics, data-splitting, and fraud-metrics lessons with tested exercises and Colab-compatible notebooks.

**Architecture:** Six lesson folders progress from arrays to model-evaluation reasoning. Python starter modules make automated feedback fast; three notebooks provide visual exploration without becoming the sole source of truth. All computations use synthetic payment data and deterministic seeds.

**Tech Stack:** Python 3.12+, NumPy, Pandas, pytest, JupyterLab, nbformat

**Spec:** `docs/superpowers/specs/2026-09-19-ai-engineer-roadmap-design.md`

## Global Constraints

- Use the global constraints and Review Focus in `2026-09-19-ai-engineer-roadmap-implementation.md`.
- Do not introduce scikit-learn in Module 03; metric fundamentals are implemented or derived with NumPy so the mechanics stay visible.
- Tests compare floating-point results with explicit tolerances and never compare DataFrames by string rendering.
- Notebooks use fixed random seeds, repository-relative paths, cleared bulky outputs, and a documented Colab upload fallback.
- Statistics explanations distinguish descriptive association from causal claims.

## Review Focus

- Empty arrays, all-missing columns, and zero denominators have documented deterministic behavior.
- Pandas transformations do not mutate caller-owned frames unless the function name and README explicitly say so.
- Joins detect unexpected cardinality expansion with `validate=` or an equivalent assertion.
- Time-based splits sort chronologically and never place a later record in the training partition than a validation/test record.
- ROC-AUC and PR-AUC reject single-class labels with a clear `ValueError` rather than returning a misleading number.

---

### Task 1: NumPy and Pandas lesson sequence

**Files:**
- Create: `modules/03_data_foundations/README.md`
- Create: `modules/03_data_foundations/01_numpy/README.md`
- Create: `modules/03_data_foundations/01_numpy/example.py`
- Create: `modules/03_data_foundations/02_pandas_core/README.md`
- Create: `modules/03_data_foundations/02_pandas_core/example.py`
- Create: `modules/03_data_foundations/03_data_quality/README.md`
- Create: `modules/03_data_foundations/03_data_quality/example.py`
- Create: `modules/03_data_foundations/04_practical_statistics/README.md`
- Create: `modules/03_data_foundations/04_practical_statistics/example.py`
- Create: `modules/03_data_foundations/05_splits_and_leakage/README.md`
- Create: `modules/03_data_foundations/05_splits_and_leakage/example.py`
- Create: `modules/03_data_foundations/06_fraud_metrics/README.md`
- Create: `modules/03_data_foundations/06_fraud_metrics/example.py`
- Create: `modules/03_data_foundations/tests/test_examples.py`

**Interfaces:**
- Produces one deterministic `main() -> None` per example.
- Produces catalog IDs `data-numpy`, `data-pandas`, `data-quality`, `data-statistics`, `data-splits`, and `data-fraud-metrics`.

- [ ] **Step 1: Write example smoke and invariant tests**

Load all six examples and call `main`. Pin a broadcasted currency conversion result, a groupby result with named aggregations, duplicate/missing-value quality counts, a median robust to an outlier, chronological split ordering, and a confusion-matrix result for a tiny labeled set.

- [ ] **Step 2: Run tests and confirm missing examples**

Run: `uv run pytest modules/03_data_foundations/tests/test_examples.py -q`

Expected: failures naming the missing lesson modules.

- [ ] **Step 3: Write concise lesson READMEs and non-solution examples**

Use the shared lesson headings. Java comparisons focus on primitive/object arrays, Stream pipelines, SQL grouping/joining, descriptive statistics in monitoring, temporal test fixtures, and service-quality metrics. Examples use support-response latency and document-classification data where the student exercises use payments, so they teach mechanics without exposing answers.

- [ ] **Step 4: Implement examples and run checks**

Run: `uv run pytest modules/03_data_foundations/tests/test_examples.py -q`

Run: `uv run ruff check modules/03_data_foundations`

Run: `uv run mypy modules/03_data_foundations --exclude 'notebooks'`

Expected: all example tests pass.

- [ ] **Step 5: Commit**

Commit with message `docs: add data foundations lesson sequence`.

### Task 2: NumPy, Pandas, and data-quality exercises

**Files:**
- Create: `modules/03_data_foundations/01_numpy/exercises/payment_matrix/README.md`
- Create: `modules/03_data_foundations/01_numpy/exercises/payment_matrix/starter.py`
- Create: `modules/03_data_foundations/01_numpy/exercises/payment_matrix/test_starter.py`
- Create: `modules/03_data_foundations/02_pandas_core/exercises/transaction_summary/README.md`
- Create: `modules/03_data_foundations/02_pandas_core/exercises/transaction_summary/starter.py`
- Create: `modules/03_data_foundations/02_pandas_core/exercises/transaction_summary/test_starter.py`
- Create: `modules/03_data_foundations/02_pandas_core/exercises/merchant_join/README.md`
- Create: `modules/03_data_foundations/02_pandas_core/exercises/merchant_join/starter.py`
- Create: `modules/03_data_foundations/02_pandas_core/exercises/merchant_join/test_starter.py`
- Create: `modules/03_data_foundations/03_data_quality/exercises/quality_report/README.md`
- Create: `modules/03_data_foundations/03_data_quality/exercises/quality_report/starter.py`
- Create: `modules/03_data_foundations/03_data_quality/exercises/quality_report/test_starter.py`

**Interfaces:**
- Produces `convert_amount_matrix(amounts: NDArray[np.float64], rates: NDArray[np.float64]) -> NDArray[np.float64]` using broadcasting and without Python loops.
- Produces `summarize_transactions(frame: pd.DataFrame) -> pd.DataFrame` with one row per currency/status, transaction count, total, median, and 95th percentile.
- Produces `attach_merchant_risk(transactions: pd.DataFrame, merchants: pd.DataFrame) -> pd.DataFrame` with many-to-one validation and unchanged transaction row count.
- Produces immutable `QualityReport` data and `assess_transaction_quality(frame: pd.DataFrame) -> QualityReport` covering missing IDs, duplicate transaction IDs, invalid amounts, invalid timestamps, and unknown categories.

- [ ] **Step 1: Write array tests**

Pin shape, dtype, broadcasting result, input immutability, empty row dimension, mismatched currency dimension, and absence of explicit loops using an AST assertion limited to the student function.

- [ ] **Step 2: Write DataFrame tests**

Use `pandas.testing.assert_frame_equal`. Pin named output columns and dtypes, missing-value policy, datetime handling, categorical grouping, deterministic sort order, input immutability, many-to-one merge validation, and duplicate merchant-key rejection.

- [ ] **Step 3: Write data-quality tests**

Pin an entirely clean frame, overlapping quality defects, invalid decimal text, timezone-naive timestamps, all-missing optional category values, and no mutation. Expected counts must derive from explicit test rows rather than fixture magic numbers.

- [ ] **Step 4: Add typed starters and exercise READMEs**

Starter docstrings define required columns, output schema, error behavior, and mutation policy. Hints name `axis`, masks, broadcasting, named aggregation, `merge(validate="many_to_one")`, `duplicated`, `to_datetime`, and categoricals without spelling out the completed pipeline.

- [ ] **Step 5: Run exercise gates and commit**

Run: `uv run pytest modules/03_data_foundations/01_numpy/exercises modules/03_data_foundations/02_pandas_core/exercises modules/03_data_foundations/03_data_quality/exercises -q -rx`

Run: `uv run ruff check modules/03_data_foundations/01_numpy modules/03_data_foundations/02_pandas_core modules/03_data_foundations/03_data_quality`

Run: `uv run mypy modules/03_data_foundations --exclude 'notebooks'`

Commit with message `feat: add NumPy and Pandas exercises`.

### Task 3: Statistics, splits, and fraud-metrics exercises

**Files:**
- Create: `modules/03_data_foundations/04_practical_statistics/exercises/statistical_profile/README.md`
- Create: `modules/03_data_foundations/04_practical_statistics/exercises/statistical_profile/starter.py`
- Create: `modules/03_data_foundations/04_practical_statistics/exercises/statistical_profile/test_starter.py`
- Create: `modules/03_data_foundations/04_practical_statistics/exercises/bayes_alert/README.md`
- Create: `modules/03_data_foundations/04_practical_statistics/exercises/bayes_alert/starter.py`
- Create: `modules/03_data_foundations/04_practical_statistics/exercises/bayes_alert/test_starter.py`
- Create: `modules/03_data_foundations/05_splits_and_leakage/exercises/time_split/README.md`
- Create: `modules/03_data_foundations/05_splits_and_leakage/exercises/time_split/starter.py`
- Create: `modules/03_data_foundations/05_splits_and_leakage/exercises/time_split/test_starter.py`
- Create: `modules/03_data_foundations/06_fraud_metrics/exercises/confusion_metrics/README.md`
- Create: `modules/03_data_foundations/06_fraud_metrics/exercises/confusion_metrics/starter.py`
- Create: `modules/03_data_foundations/06_fraud_metrics/exercises/confusion_metrics/test_starter.py`
- Create: `modules/03_data_foundations/06_fraud_metrics/exercises/ranking_metrics/README.md`
- Create: `modules/03_data_foundations/06_fraud_metrics/exercises/ranking_metrics/starter.py`
- Create: `modules/03_data_foundations/06_fraud_metrics/exercises/ranking_metrics/test_starter.py`

**Interfaces:**
- Produces `describe_amounts(values: NDArray[np.float64]) -> StatisticalProfile` with mean, median, population variance, population standard deviation, and selected percentiles.
- Produces `fraud_probability_given_alert(base_rate: float, sensitivity: float, false_positive_rate: float) -> float`.
- Produces `chronological_split(frame: pd.DataFrame, train_fraction: float, validation_fraction: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]`.
- Produces `confusion_counts`, `accuracy`, `precision`, `recall`, and `f1` with an explicit `zero_division` policy.
- Produces `roc_auc(labels, scores) -> float` and `pr_auc(labels, scores) -> float` with tie handling and single-class rejection.

- [ ] **Step 1: Write descriptive-statistics and Bayes tests**

Pin outlier sensitivity of mean versus median, population variance convention, percentile values, empty/all-NaN rejection, posterior probability for a rare-event example, zero alert probability, and all input probabilities outside `[0, 1]`.

- [ ] **Step 2: Write chronological split tests**

Pin stable timestamp sorting, exact partition sizes under the README's rounding rule, no input mutation, invalid fraction sums, duplicate timestamp stability, and the invariant `max(train.timestamp) <= min(validation.timestamp) <= min(test.timestamp)` where partitions are non-empty.

- [ ] **Step 3: Write confusion and ranking metric tests**

Pin TP/FP/TN/FN, perfect and all-negative predictors, the 99.9%-accurate zero-recall scenario with 1 fraud among 1,000 rows, zero denominators, tied scores, score-order invariance, known ROC-AUC and PR-AUC values, length mismatch, non-binary labels, out-of-range scores, and single-class rejection.

- [ ] **Step 4: Add starters and reasoning prompts**

The fraud README requires a written answer explaining why accuracy is useless in the imbalanced example and when PR-AUC is more informative than ROC-AUC. The Bayes README requires substituting the supplied banking-alert rates before coding. No answer text is supplied.

- [ ] **Step 5: Run tests and commit**

Run: `uv run pytest modules/03_data_foundations/04_practical_statistics modules/03_data_foundations/05_splits_and_leakage modules/03_data_foundations/06_fraud_metrics -q -rx`

Run: `uv run ruff check modules/03_data_foundations`

Run: `uv run mypy modules/03_data_foundations --exclude 'notebooks'`

Commit with message `feat: add statistics and fraud metric exercises`.

### Task 4: Colab-compatible notebooks and notebook contracts

**Files:**
- Create: `modules/03_data_foundations/notebooks/01_numpy_payment_arrays.ipynb`
- Create: `modules/03_data_foundations/notebooks/02_pandas_transaction_analysis.ipynb`
- Create: `modules/03_data_foundations/notebooks/03_fraud_metrics.ipynb`
- Create: `modules/03_data_foundations/notebooks/README.md`
- Create: `modules/03_data_foundations/tests/test_notebooks.py`

**Interfaces:**
- Consumes: `datasets/transactions.csv` once Banking Task 1 creates it.
- Produces valid notebook version 4 files with Python 3 kernelspec metadata and a `DATA_PATH` fallback cell.

- [ ] **Step 1: Write notebook structure tests**

Use `nbformat.read(..., as_version=4)`. Assert each notebook has a title Markdown cell, learning goals, setup cell, at least three code cells, at least three student exercise cells tagged `exercise`, a final self-check, Python 3 kernelspec metadata, no absolute local paths, and no stored output larger than 20 KB.

- [ ] **Step 2: Run tests and observe missing-notebook failures**

Run: `uv run pytest modules/03_data_foundations/tests/test_notebooks.py -q`

- [ ] **Step 3: Create the notebooks**

Notebook 1 demonstrates shape, masks, broadcasting, aggregation by axis, and a dot-product risk score using data distinct from `payment_matrix`. Notebook 2 demonstrates inspection, `loc`/`iloc`, missing values, duplicates, groupby, merge, sorting, datetimes, transformations, and categoricals. Notebook 3 demonstrates confusion-matrix interpretation and the 99.9% accuracy trap but leaves metric exercise cells unfinished.

Every exercise cell raises `NotImplementedError("Complete this notebook exercise")` after its instructions so accidental execution cannot look complete.

- [ ] **Step 4: Run the full Module 03 gate**

Run: `uv run pytest modules/03_data_foundations -q -rx`

Run: `uv run ruff check modules/03_data_foundations`

Run: `uv run ruff format --check modules/03_data_foundations --exclude '*.ipynb'`

Run: `uv run mypy modules/03_data_foundations --exclude 'notebooks'`

Expected: examples and notebook contracts pass; student code remains visibly expected-incomplete.

- [ ] **Step 5: Commit**

Commit with message `feat: add data learning notebooks`.
