# Module 04 — Machine Learning

## Как проходить углублённую теорию (пакет 4)

Откройте [01 Problem framing](01_problem_framing/README.md), затем его русскую
теорию. Двигайтесь по существующим урокам 01 → 02 → 03 → 04 → 05 → 06:
сначала прогноз и ручной пример, затем запуск, собственная вариация и прежнее
упражнение. Ссылки на `theory.md` стоят в каждом README; ID и prerequisites
не изменены. До обучения нужны NumPy/Pandas/качество данных и статистика
из Module 03 — [пакет 3](../03_data_foundations/04_practical_statistics/README.md)
повторно не переписывается.

В уроке 06 есть [две преподавательские демонстрации](06_reproducibility/theory.md)
с реальным fit, выбором на development, замороженным test и save/reload.
Из корня проекта, после `uv sync --locked`, выберите **новую** папку:

```powershell
uv run --offline --no-sync python -m modules.04_machine_learning.06_reproducibility.classical_demo --output reports/classical-demo-01
```

Для необязательных графиков: `uv sync --locked --group visualization`, затем
та же команда с `--plots` и **другим новым** именем папки. Запуск не скачивает
модели/датасеты и не заполняет ученические отчёты. Baseline, малая synthetic
выборка и успешные tests не доказывают качество на реальных данных.

Существующие задания: `ml-group-safe-split`, `ml-mixed-feature-pipeline`,
`ml-model-comparison`, `ml-threshold-policy`, `ml-evaluation-report`; далее
[самостоятельное исследование](exercises/tabular_study/README.md) и
[открытый контроль оценки](exercises/evaluation_case/README.md) согласно их
prerequisites. `test ID` допускает незавершённые xfail; `check ID` требует
реализации **этого** прежнего контракта. Ответы на вопросы теории проверяются
вручную; новых автоматических зачётов текста нет.

Затем [07 Training bridge](07_training_bridge/README.md) →
[PyTorch](../../labs/01_pytorch_foundations/README.md). Механика kNN в уроке 04
понятна до моста, но самостоятельный `ml-knn-mechanics` сохраняет prerequisite
`ml-training-bridge`. Сопровождение [PyTorch](../../labs/01_pytorch_foundations/theory.md)
и [HF/Transformers](../../labs/02_huggingface_models/theory.md) уже подготовлено
в пакете 5; это не означает выполненную ученическую лабораторную.

[Покрытие пакета 4](../../docs/wave2-coverage.md#theory-packet-4) ·
[Проверки и ограничения](../../docs/theory-packet-4-verification.md).

## Goal

Turn a prediction question into a defensible supervised-learning experiment. Use small,
local datasets about parks, plants, weather and sensors; no downloads or API keys are needed.

## Prerequisites

Нужны Python core (collections, functions, typing, I/O и testing) и Data Foundations:
NumPy/Pandas, качество данных, статистика, split/leakage и метрики. Умейте читать
табличные данные и объяснять дисбаланс классов и ограничения accuracy.
Module 02 (backend/API) можно проходить параллельно: он понадобится для serving,
но не является условием первого ML-эксперимента или PyTorch lab.

## Java mental model

An estimator looks like a service with `fit` and `predict`, but `fit` changes learned state.
Treat preprocessing and the estimator as one trainable component, with an explicit evaluation contract.

## Python model

Use scikit-learn estimators, `Pipeline`, `ColumnTransformer`, and explicit splitters.
Fit on training rows, select on validation folds, and inspect the reserved test set only
after the design and decision threshold are frozen. A seed is one part of reproducibility.

## Key concepts

| Lesson | Main question | Practice |
| --- | --- | --- |
| [01 Problem framing](01_problem_framing/README.md) | What is predicted, when, and against which baseline? | Write a prediction contract, then model comparison |
| [02 Validation](02_validation/README.md) | What must be unseen at evaluation time? | [Group-safe sensor split](02_validation/exercises/group_safe_split/README.md) |
| [03 Preprocessing](03_preprocessing/README.md) | What does the model learn from each fold? | [Mixed park-visit pipeline](03_preprocessing/exercises/mixed_feature_pipeline/README.md) |
| [04 Models](04_models/README.md) | Is extra complexity justified? | [Validation model comparison](04_models/exercises/model_comparison/README.md) |
| [05 Evaluation](05_evaluation/README.md) | Where and how does the model fail? | Error-slice interpretation, then evaluation report |
| [06 Reproducibility](06_reproducibility/README.md) | Can another person reproduce and trust the result? | [Reproducible evaluation report](06_reproducibility/exercises/evaluation_report/README.md) |
| [07 Мост к обучению](07_training_bridge/README.md) | Как loss и градиент связывают NumPy с autograd? | Один векторный шаг; затем [PyTorch lab](../../labs/01_pytorch_foundations/README.md) |

## Example

Run from the repository root after `uv sync`:

```powershell
uv run python modules/04_machine_learning/01_problem_framing/example.py
uv run pytest modules/04_machine_learning
uv run mypy -p modules.04_machine_learning
```

Every lesson has a standalone deterministic `example.py`. Numeric directory names work
with package-mode mypy; exercise tests use local package imports and pytest importlib mode.

## Exercises

The seven original lesson exercises are **Difficulty: Medium**, each approximately 45–75 minutes. Their
READMEs define validation rules, edge cases and focused test commands. Untouched boundaries
raise `NotImplementedError` and are expected-incomplete; an incorrect implementation fails.
Examples teach related mechanics on separate inputs and do not implement the exercise contracts.

Additional practice after the related lessons:

| Lesson connection | New practice |
| --- | --- |
| Validation | [Chronological weather split with a gap](exercises/time_series_split/README.md) |
| Evaluation | [Explicit-label wildlife classification report](exercises/multiclass_report/README.md) |
| Evaluation | [Weather-alert threshold policy](exercises/threshold_policy/README.md) |

## Self-check

1. Which fields are available at the exact prediction time?
2. Why can random row splits overestimate performance for repeated sensors?
3. Where must imputation and scaling run during cross-validation?
4. Why is the winning validation score not an unbiased final test estimate?
5. What must accompany a model artifact besides a random seed?

## Done when

You can run the six original examples and the training-bridge example, complete the seven
original exercises plus the bridge task, justify a baseline and split, explain an error slice,
and hand another person a versioned report with data provenance.

## Математическая глубина и независимый проект

Обязательные продолжения ML-маршрута:

- [Градиенты MSE/BCE и L2](exercises/gradient_derivations/README.md).
- [Линейная геометрия, Ridge и PCA](exercises/linear_geometry/README.md).
- [Decision stump и шаги boosting](exercises/tree_boosting/README.md).
- [Внешний tabular проект](../../projects/external_tabular/README.md).

Prerequisites, проверки и следующий этап — в [текущей карте](../../docs/learning-map.md).
