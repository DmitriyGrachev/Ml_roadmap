# Compare paired model losses

Сложность: средняя · 60–90 минут. Это отдельное упражнение; зачёт прежних лабораторных работ от него не зависит.

## Перед началом

- `data-statistics`: [описательная статистика](../../04_practical_statistics/README.md).
- `data-paired-observations`: [согласованные пары](../paired_observations/README.md).
- `ml-validation`: [разбиение без утечки](../../../04_machine_learning/02_validation/README.md).
- `ml-evaluation`: [оценка моделей](../../../04_machine_learning/05_evaluation/README.md).

## Задача

Реализуйте `paired_difference` в `starter.py`. Для каждой строки даны потери моделей A и B на **одном и том же** наблюдении и ID независимого объекта. Разность строки — `loss_b - loss_a`: отрицательное значение означает меньшие потери B. Если у объекта несколько строк, сначала усредните его разности; итоговый эффект — среднее этих средних с **одинаковым весом каждого объекта**. Объекты сортируются по ID для воспроизводимого порядка. Строки нельзя независимо переставлять или фильтровать: это разрушит пары.

`DifferenceEstimate(effect, lower, upper, unit_count, resample_count)` содержит оценку и percentile bootstrap интервал. В каждом повторе `np.random.default_rng(seed).integers(0, unit_count, size=unit_count)` выбирает целые объекты с возвращением; используйте `float64` и `np.quantile` с обычной линейной интерполяцией на уровнях `(1-confidence)/2` и `1-(1-confidence)/2`. Требуются хотя бы два независимых ID, конечные числа и совпадающие непустые длины, непустые строковые ID, `n_resamples >= 100`, целый неотрицательный `seed`, `0 < confidence < 1`. Неверный ввод вызывает `ValueError`.

Повторные ID допустимы: события одного объекта могут зависеть друг от друга. Для временного ряда сначала обоснуйте независимую единицу (например, устройство или целый временной блок); отдельные соседние события нельзя объявить IID только ради узкого интервала.

## Короткий пример и интерпретация

`example.py` сравнивает точность двух датчиков на трёх измерениях, два из которых принадлежат одному датчику. Это законченный пример **другой задачи**, без готового сравнения ваших моделей. Запуск: `.venv/Scripts/python.exe -m modules.03_data_foundations.exercises.paired_model_comparison.example`.

Интервал описывает неопределённость оценённой разности при выбранных единицах и процедуре отбора. Он не заменяет размер эффекта и порог практической пользы, который следует задать до просмотра результата. Сравните также срезы и их поддержку: общий выигрыш может скрывать ущерб в важной группе, а крошечный срез даёт слабое свидетельство. Выбор модели по validation и вывод о её качестве на отложенной выборке — разные шаги; многократный выбор по test превращает его в validation.

## Сохранённое свидетельство

`evidence.validate_evidence(root)` проверяет каталог JSON, не вызывает student `starter.py` и ничего в нём не меняет. Пример контракта для собственного эксперимента:

- `manifest.json`: `schema_version: 1`, `exercise_id: "data-paired-model-comparison"`, SHA-256 полей `dataset_sha256`, `split_sha256`, `predictions_sha256`, `resamples_sha256`; `config` с `seed`, `n_resamples`, `confidence`, `loss` (`absolute_error` или `squared_error`) и `unit_policy: "cluster_by_unit_id"`; `effect`, `lower`, `upper`, `unit_count`, `resample_count`.
- `snapshot.json`: массив уникальных `{row_id, unit_id, label}`; `split.json`: `evaluation_row_ids` в порядке оценки, ссылающиеся на этот snapshot.
- `predictions.json`: по одной строке в порядке split, `{row_id, prediction_a, prediction_b, loss_a, loss_b}`. Проверка пересчитает оба loss из label и prediction.
- `resamples.json`: отсортированные `unit_ids` и `indices` формы `[n_resamples][unit_count]`. Проверка воспроизведёт seed, средние по объектам, эффект и границы интервала.

Хеши проверяют сохранённые байты и согласованность артефактов. Честность происхождения snapshot и качество выбора тестового разбиения требуют отдельной проверки человеком.

## Работа и критерий

Меняйте только `starter.py`; `test_starter.py`, `evidence.py` и примеры являются учебным контрактом. Подсказки по этапам: (1) проверьте выравнивание и конечность; (2) накопите разности внутри ID; (3) повторно выбирайте ID, а не строки; (4) проверьте постоянную разность и кластеры разного размера.

Из корня репозитория:

```powershell
.venv/Scripts/python.exe scripts/learn.py test data-paired-model-comparison
.venv/Scripts/python.exe scripts/learn.py check data-paired-model-comparison
.venv/Scripts/python.exe -m pytest modules/03_data_foundations/exercises/paired_model_comparison -q -rx
```

Unit tests проверяют формулы и ошибки ввода; пример — только локальный smoke; реальная ML evaluation требует сохранённых predictions и отложенного split; объяснение единицы, порога пользы и срезов требует review. До реализации TODO `test` показывает xfail, а `check` не засчитывает упражнение. Готово, когда все обязательные тесты проходят без xfail и вы можете объяснить, почему строковый bootstrap здесь ошибочен.
