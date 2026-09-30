# Linear models, trees and validation-based selection

## Goal

Compare a simple baseline with models of increasing flexibility using the same folds
and the same metric. Select hyperparameters without consulting the reserved test set.

## Java mental model

Models are interchangeable implementations of `fit`/`predict`, but their assumptions
are not interchangeable. A more elaborate implementation does not automatically improve
the service's behavior on unseen requests.

## Python model

Ridge regression regularizes linear coefficients and benefits from comparable feature
scales. Logistic regression is a classifier despite its name. Trees learn thresholds
and interactions without scaling, but an unrestricted tree can memorize training rows.
`cross_validate` exposes per-fold scores; `GridSearchCV` selects a parameter setting.

## Key concepts

- Linear models provide a useful baseline when effects are roughly additive.
- Trees capture nonlinear boundaries; depth and minimum leaf size control flexibility.
- Use identical folds for comparisons, and keep preprocessing inside each candidate pipeline.
- Scikit-learn maximizes scores: `neg_mean_absolute_error` must be negated for reported MAE.
- The selected CV score is optimistic after trying many alternatives. Evaluate the frozen
  choice on a test set; use nested CV when estimating the entire selection procedure.

References: [linear models](https://scikit-learn.org/stable/modules/linear_model.html),
[trees](https://scikit-learn.org/stable/modules/tree.html),
[cross_validate](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.cross_validate.html),
and [GridSearchCV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html).

## Example

```powershell
uv run python modules/04_machine_learning/04_models/example.py
```

A tiny generated plant-classification example searches tree depth using stratified
development folds. A disjoint test set is scored once after selection. The exercise
instead compares three regression candidates and returns fold-level MAE summaries.

## Exercises

### Короткое продолжение: bagging, Random Forest и boosting

Неустойчивое дерево меняется при небольшом изменении train. Bagging обучает несколько
моделей на bootstrap-выборках train и объединяет предсказания. Эти модели не исправляют
друг друга последовательно; усреднение может уменьшить разброс, если ошибки не полностью
совпадают. В Random Forest дополнительно ограничивается случайный набор признаков,
рассматриваемых при каждом split: это помогает разнообразить деревья.
`RandomForestClassifier` усредняет вероятности деревьев, затем выбирает класс.
`n_estimators` задаёт число деревьев, `max_features` — число рассматриваемых признаков;
глубина и минимальный лист по-прежнему ограничивают сложность каждого дерева.
[Документация RF](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html).

Gradient boosting строит аддитивную модель последовательно: новый небольшой learner
использует градиент loss текущего ансамбля, поэтому зависит от предыдущих шагов.
`learning_rate` уменьшает вклад каждого шага; `max_iter` задаёт бюджет шагов у
`HistGradientBoostingClassifier`. Histogram-вариант группирует значения признаков
в bins для поиска split. Добавление шагов не гарантирует улучшения validation loss;
важен совместный выбор learning rate, сложности дерева и числа шагов.
[Механика ансамблей](https://scikit-learn.org/stable/modules/ensemble.html),
[API histogram boosting](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).

В [sensor example](../exercises/tabular_study/example.py) функция
`compare_sensor_ensembles(seed=11)` обучает дерево, лес из восьми деревьев и восемь
шагов boosting на одних 64 строках, затем смотрит 16 development validation строк.
Она показывает различие вероятностей деревьев, равенство их среднего вероятности
леса и validation Brier после каждого шага boosting. Это маленькая демонстрация
механики: test здесь не используется, победитель по качеству не предписан.
Запуск и самостоятельная обязательная вариация — в
[табличном упражнении](../exercises/tabular_study/README.md#мини-практика-ансамблей).

Complete [validation model comparison](exercises/model_comparison/README.md), including
a dummy baseline, independent preprocessing per fold and reproducible fold ordering.
Для ручной проверки расстояний и ничьих отдельно пройдите
[геометрию kNN](../exercises/knn_mechanics/README.md); старое сравнение моделей не меняется.
Далее [самостоятельное табличное исследование](../exercises/tabular_study/README.md)
объединяет ограниченный поиск, calibration и проверяемый эксперимент.

## Self-check

1. Why can an unrestricted tree have perfect training accuracy and poor validation accuracy?
2. Why must all candidates share validation folds?
3. What does a negative MAE scorer mean, and which direction is better?

## Done when

You can justify a model against its baseline, report validation variability, and distinguish
the selection score from a final estimate of generalization.
