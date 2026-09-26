# Mixed-feature park-visit pipeline

Difficulty: Medium

Estimated time: 60–75 minutes. Prerequisites: preprocessing lesson, regression framing.

Build a pipeline that predicts visits from weather measurements and park category. The
caller will fit it separately inside each training fold; your factory must return it unfitted.

## Contract

Implement `build_visit_pipeline(numeric_features, categorical_features)`:

- Both lists must contain at least one nonempty, non-whitespace string. Reject duplicates
  within or across lists with `ValueError` mentioning `feature` or `column`.
  Preserve names exactly; do not strip or rename them.
- Return a fresh `sklearn.pipeline.Pipeline` with steps `preprocess` and `model`.
- `preprocess` is a `ColumnTransformer` with named branches `num` and `cat`, selecting
  the provided columns in their given order. Set `remainder="drop"`.
- `num` is a pipeline: `imputer=SimpleImputer(strategy="median", keep_empty_features=True)`
  then `scaler=StandardScaler()`. Entirely missing training columns remain present and are
  filled with zero by the numeric imputer.
- `cat` is a pipeline: `imputer=SimpleImputer(strategy="constant", fill_value="__missing__",
  keep_empty_features=True)` then `encoder=OneHotEncoder(handle_unknown="ignore",
  sparse_output=False)`. Callers supply categorical columns with `object` dtype,
  containing strings or `numpy.nan` (not `None`), at both fit and prediction time.
  This schema also applies when every value in a categorical column is missing.
- `model` is `Ridge(alpha=1.0, solver="svd")`, making the small dense example deterministic.
- Fitting or predicting must not mutate input frames or the original feature lists.
  The pipeline must ignore extra columns, including a target accidentally retained in `X`.

The names are a public inspection interface: reviewers can audit imputer statistics and
encoder categories. Do not prefit or return a global shared pipeline. Unknown categories
must be accepted; that does not imply that they are well represented by training data.

Pandas may infer a numeric dtype for an all-NaN column. A string imputation value cannot
be inserted into that numeric column, so declare its intended categorical dtype explicitly.
For example, prepare a caller-owned copy with `frame = frame.astype({"park": object})`.
This is a schema declaration, not a statistic learned from validation rows. An entirely
missing categorical training column must remain present and learn `"__missing__"` as
its sole encoded category; new string categories then use the encoder's unknown-value rule.

## Edge cases

Missing numeric and categorical values, numeric or object-typed categorical columns
missing throughout training, unseen categories, misleading extra columns, independent
factory calls and extreme validation measurements that must not change fitted state.

## Run

```powershell
uv run pytest modules/04_machine_learning/03_preprocessing/exercises/mixed_feature_pipeline -q
```

Done when the pipeline passes behavior checks and you can point to the exact training
fold that supplied each imputation statistic, scaling mean and category vocabulary.
