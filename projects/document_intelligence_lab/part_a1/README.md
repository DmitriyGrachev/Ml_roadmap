# A1: воспроизводимый эксперимент с документами

Научитесь переносить эксперимент в новый каталог и процесс так, чтобы данные,
preprocessing, модель и пересчитанные метрики по-прежнему описывали один run.
Это вводная часть проекта; полная часть A требует дальнейшей PyTorch/HF работы.

Перед началом нужны [NumPy](../../../modules/03_data_foundations/01_numpy/README.md),
[split и leakage](../../../modules/04_machine_learning/02_validation/README.md),
[preprocessing](../../../modules/04_machine_learning/03_preprocessing/README.md),
[оценка и uncertainty](../../../modules/04_machine_learning/05_evaluation/README.md),
[воспроизводимость](../../../modules/04_machine_learning/06_reproducibility/README.md).
Повторите самостоятельные `data-release-study`, `ml-tabular-study`,
`data-paired-model-comparison` и `ml-evaluation-case`; A1 не заменяет эти задания.

Прочитайте [разбор](theory.md), [правила аннотации](fixtures/annotation-guide.md)
и [контракт файлов](schema.md). Teacher использует 21 авторское описание фигур;
в [самостоятельной работе](exercise/README.md) — 18 других объявлений библиотеки.

Из корня репозитория, в существующей базовой среде:

```powershell
.venv/Scripts/python.exe -m projects.document_intelligence_lab.part_a1.demo --output C:/Temp/document-a1-run-001
.venv/Scripts/python.exe -m pytest projects/document_intelligence_lab/part_a1/test_demo.py -q
```

`--output` обязателен и должен быть новым каталогом. Не указывайте папку ученика.
Запуск создаёт `rules/`, `tfidf-linear/` и `comparison.json`. Сохранённый sklearn
Pipeline содержит fitted TF-IDF и LogisticRegression; fit использует только train.
Два фиксированных кандидата сравниваются на validation, tie решает имя метода;
после выбора оба получают один test. Модель не переобучается на validation/test.
`comparison.json` указывает выбранный метод и реальные test metrics обоих кандидатов.

Синтетический teacher показывает accuracy `2/3` у неполных rules и `1` у TF-IDF.
Это проверка механики на очень простой лексике, а не качество на реальных документах.
Timings измеряются заново в секундах на CPU; memory остаётся `null` с причиной.
Каждый запуск имеет новый run ID. Повторяемость означает одинаковые test predictions
при тех же bytes/config/среде, а не одинаковое время исполнения или manifest hash.

Проверка перечитывает все bytes и метрики; loader заново получает predictions.
Author tests перемещают каталог и запускают inference в новом процессе.
JSON rules не исполняет Python. Pickle исполняет код: только оператор заранее
выбирает доверенный локальный bundle и внешний expected manifest SHA-256.
Hash удостоверяет сохранность bytes, но не доверие к их автору.

[CI и границы доказательств](../../../docs/continuous-integration.md): зелёный job
подтверждает проверенные механизмы в его среде. Hosted CI run, pretrained quality
и освоение ученика требуют отдельных свидетельств. Зелёный pytest сам по себе
не означает освоение A1 и не завершает полный Document Intelligence проект.
