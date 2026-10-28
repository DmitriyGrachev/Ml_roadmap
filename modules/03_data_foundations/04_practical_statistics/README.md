# Practical statistics

## Goal

Describe a distribution honestly and distinguish an observed association from a causal explanation.

Начните с [теории и разобранных примеров](theory.md): одна строка данных,
описание распределения, условная вероятность и парные измерения. Для чтения
нужны [NumPy](../01_numpy/theory.md) и представление о
[качестве данных](../03_data_quality/theory.md); будущие ML-уроки не требуются.

## Java mental model

Statistics is not a utility-method afterthought: choosing mean, median, variance, or a percentile is a product and monitoring decision, not an interchangeable calculation.

## Python model

Use NumPy aggregations on a well-defined sample, inspect outliers, and communicate what a summary cannot prove.

В [теории](theory.md) показаны ручной расчёт и отдельные запускаемые фрагменты.
Дополнительная teacher-демонстрация строит графики необычного значения и
изменчивости выборочного среднего; графики не являются результатом student TODO.

## Key concepts

Mean, median, population variance, standard deviation, percentiles, distributions, correlation, conditional probability, and Bayesian intuition.

## Example

`example.py` uses median support-response latency so one unusually slow response does not dominate the typical value.
Разбор этого массива и смысла медианы находится в [теории](theory.md).

Сначала запишите прогноз из §2 и §8 теории. Из корня проекта, без записи файлов:

```powershell
uv run --offline --no-sync python -m modules.03_data_foundations.04_practical_statistics.stats_demo
```

Графики необязательны: готовые PNG встроены в теорию. Для собственного повторения
подготовьте существующую группу и укажите **новую** папку:

```powershell
uv sync --locked --group visualization
uv run --offline --no-sync python -m modules.03_data_foundations.04_practical_statistics.stats_demo --output reports/stats-demo-01
```

Экспорт сохраняет `outlier.png`, `sampling.png`, CSV и `metadata.json`.
Существующий каталог не перезаписывается; данные и модели не скачиваются.

## Exercises

Later exercises use their own payment-alert inputs for a statistical profile and Bayes calculation; this lesson supplies mechanics, not answers.

После самостоятельной попытки используйте [Statistical amount profile](exercises/statistical_profile/README.md)
(`data-statistical-profile`) для описательных статистик и
[Fraud probability after an alert](exercises/bayes_alert/README.md)
(`data-bayes-alert`) для знаменателя условной вероятности. Для парных
измерений есть [Summarize paired observations](../exercises/paired_observations/README.md)
(`data-paired-observations`): там совместная фильтрация пар и *выборочная*
ковариация, в отличие от дисперсии всей переданной совокупности в профиле.

Позднее, после [разбиения без утечки](../../04_machine_learning/02_validation/README.md)
и [оценки моделей](../../04_machine_learning/05_evaluation/README.md), переходите к
[парному сравнению потерь моделей](../exercises/paired_model_comparison/README.md).
[Рандомизированный A/A–A/B пример](../exercises/randomized_experiment/README.md)
продолжает тему единицы наблюдения после этого сравнения. Они не нужны для
нынешнего урока.

## Дизайн эксперимента: продолжение

После независимой единицы и случайного назначения прочитайте
[дизайн эксперимента](experiment_design.md): эффект, confidence interval, p-value,
MDE, power и размер двух групп; затем A/A–A/B симуляция показывает, как
подглядывание и множество проверок меняют риск ложных выводов. Демонстрация
работает в основном окружении без сети и новых зависимостей:

```powershell
uv run --offline --no-sync python -m modules.03_data_foundations.04_practical_statistics.experiment_demo
```

В [самостоятельной практике](../exercises/experiment_design/README.md)
(`data-experiment-design`) отдельно реализуйте маленький контракт множественных
проверок и проведите собственную заранее спланированную симуляцию. Успех unit
tests не засчитывает отчёт и объяснение статистических ограничений.

## Self-check

1. Why can median be more robust than mean?
2. What does a percentile communicate?
3. Which variance convention is being used?
4. Why does correlation not prove causation?
5. What information is required for a conditional probability?

Попробуйте также вопросы с новыми входами в [теории](theory.md#8-проверка-перенос-и-источники).

## Done when

You can select a descriptive statistic for a monitoring question and state its limitation.
