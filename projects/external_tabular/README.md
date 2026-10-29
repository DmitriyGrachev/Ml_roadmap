# Независимый проект: качество вина на внешних tabular данных

ID: **`ml-external-tabular`**. Это обязательное исследование после основ ML;
материалы и авторский пример готовы, работа ученика ещё не выполнена.
Ориентир — 3–5 занятий с защитой. Предсказание `quality >= 6` — учебная
бинаризация порядковой оценки, а не медицинский, производственный или рыночный совет.

Нужны [validation](../../modules/04_machine_learning/02_validation/README.md),
[preprocessing](../../modules/04_machine_learning/03_preprocessing/README.md),
[выбор моделей](../../modules/04_machine_learning/04_models/README.md),
[оценка](../../modules/04_machine_learning/05_evaluation/README.md), работа с CSV,
`pathlib`, функциями, словарями, `Pipeline`, confusion matrix и Git.
Запускайте команды из корня репозитория; в PyCharm задайте корень как working directory
и интерпретатор `.venv`. Команды `uv run python ...` одинаковы в PowerShell и Linux.

## Задача и критерий результата

Вы — разработчик сервиса, который получает результаты физико-химических измерений
**до** сенсорной оценки. Нужно предсказать, окажется ли итоговая оценка не ниже 6.
Выбираете и обосновываете split, обучаете baseline и две разные model families,
сравниваете качество с неопределённостью и объясняете, что придётся изменить при
переходе на другую популяцию. Победа дерева над линейной моделью не обязательна.

Источником основного маршрута служит
[UCI Wine Quality](https://archive.ics.uci.edu/dataset/186/wine+quality),
файл **winequality-red.csv**: 11 измерений и поле `quality`.
Карточка UCI описывает красное/белое vinho verde из северной Португалии,
дисбаланс и порядковый target; это ограничивает выводы о другом регионе/годе/вине.
[Лицензия UCI CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
требует attribution. Сохраните ссылку на карточку, авторов/публикацию Cortez et al.
из неё, дату получения, название файла, исходные байты и описание изменений.
Проверка ресурсов для этой методички: 28.10.2026 UTC. При другом источнике сначала
нужен новый документированный адаптер и проверяемый контракт, а не замена URL в JSON.

Скачивание выполняйте **отдельным явным действием**. Default pytest не обращается к сети.
Можно сохранить CSV по ссылке
[UCI red CSV](https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv)
в `projects/external_tabular/submission/raw.csv`; либо скачать ZIP из карточки UCI
и извлечь только этот CSV. Не переименовывайте белое вино в красное.
Папка `submission/` игнорируется Git. Весов, данных, результатов и готового ученического
отчёта в исходниках нет. Не распространяйте производные данные без проверки лицензии.

## Что именно нужно исследовать

До обучения напишите постановку в своём `analysis.md`: объект предсказания,
момент доступности X, стоимость FP/FN, пользователь результата и границы применения.
Отдельно объясните, чем `quality>=6` отличается от multiclass/regression и почему
threshold не был выбран по final test. ID, номер строки, `quality` и вычисленный
из `quality` класс не могут быть признаками. Проверка доступности нужна для каждого
из 11 измерений: что уже измерено к моменту запроса сервиса и сколько это стоит?

`prepare_records(raw_bytes)` в [protocol.py](protocol.py) — готовый **парсер**,
не решение исследования. Он проверяет точные заголовки, конечность чисел,
диапазон target; воспроизводимо выводит бинарные labels. `row_id` включает
префикс SHA-256 исходного CSV и индекс строки. `group_id` — SHA-256 нормализованных
числовых признаков без target: одинаковые X не могут пересечь train/dev/test,
даже если исходные строки различаются форматированием или меткой.
Сохраняются все строки. Не удаляйте сложные строки после просмотра ошибок test.

Аудитируйте missingness, диапазоны, распределения и частоты классов; посчитайте
точные дубликаты X, дубликаты X+y и одинаковые X с разными y. Последнее может быть
шумом измерения/разметки. Группировка одинаковых X не доказывает независимость:
нет надёжного ID производителя/партии и времени, поэтому temporal generalization
и отсутствие batch leakage по этому CSV доказать нельзя. Это обязательное ограничение.
Нельзя выдумать дату/producer из номера строки и назвать split временным.

Сделайте manifest **до выбора моделей**: ориентир 60/20/20 по группам,
стратификация насколько возможна, seed, фактические количества строк/групп/классов.
Препроцессинг fit только train. Dev называется `validation`, final holdout — `test`.
Все группы и строки назначаются ровно одному split; точные feature-дубликаты
остаются вместе. Если групп нет в другом выбранном источнике, обоснуйте IID split;
если есть время/клиент/устройство, split должен отражать этот механизм.
Зафиксируйте SHA-256 `splits.json` и правило отбора, затем не используйте test
для выбора C, depth, feature selection, threshold или бюджета.

Три обязательных метода на **одних test ID**:

| Метод | Минимальная реализация | Что обсуждать |
| --- | --- | --- |
| `dummy` | `DummyClassifier(strategy="most_frequent")` | Accuracy при дисбалансе; что значит нулевой recall меньшинства |
| `linear` | `Pipeline(StandardScaler(), LogisticRegression(...))` | Train-only scaler, C/L2, коэффициенты и коррелированные измерения |
| `tree` | Ограниченное дерево или tree ensemble | Нелинейности, max_depth/min_samples_leaf, variance и overfitting |

Заранее задайте небольшой поиск, например C ∈ {0.1, 1, 10} и max_depth ∈ {2, 4, 6}.
Выберите настройку по validation macro-F1, затем latency/простоте при ничьей.
Это пример бюджета, не обязательный список лучшей модели. Запишите все попытки,
включая неудачные. Не выбирайте метод по final test, даже если он там выиграл.
Укажете preprocessing, Python/NumPy/scikit-learn versions, Git SHA, seed,
полные configs и измеренное время с границей измерения. Если рабочее дерево грязное,
сохраните patch/копию изменённых исходников, поскольку SHA коммита их не включает.

## Неопределённость, ошибки и повторное обучение

В `evaluation.json` сохраняйте final labels, predictions, confusion matrix, accuracy,
macro-F1, длительность и ID в порядке locked test. Все классы включаются в macro-F1,
`zero_division=0`. Сравните `linear` и `tree` попарно. Утилита `paired_bootstrap`
делает 1000 **парных** выборок строк seed=17 и сохраняет разность macro-F1 candidate−baseline
и 2.5/97.5 percentiles (индексы 24 и 974 в отсортированных 1000 значениях).
Оба метода получают одинаковые resampled indices. Это условный интервал при
фиксированных предсказаниях и предположении IID строк. Он не измеряет разброс
от нового обучения, split или нового региона; если группы зависимы, отдельно
реализуйте cluster bootstrap и объясните, как меняется интерпретация.

Отдельно **полностью переобучите** linear и tree минимум с тремя разными seeds.
Сохраните их validation predictions/labels/configs/logs, а не три bootstrap-таблицы
одного fit. Сравнение делайте на одном locked validation наборе; оценивайте,
какая часть разброса исчезает у детерминированного алгоритма и почему.
Для sampling/split sensitivity проведите дополнительное исследование на train/dev,
не перебирайте seeds ради лучшего final test. Укажите среднее, min/max или SD,
число повторов и реальный compute; три повтора не дают надёжной оценки хвостов.

Нужны минимум два проверяемых error slices. `make_evaluation` создаёт срезы по true
class для проверки арифметики, но в собственной работе добавьте практически полезные
срезы: низкий/высокий alcohol по **train-derived** границе, пограничная истинная
quality 5/6, редкие диапазоны измерений. Для каждого сохраните имя, точные test ID,
метрики каждого метода, count и интерпретацию. True quality — допустимый
**аудитный** срез после оценки, но не признак и не routing feature сервиса.
Пересечения срезов допустимы, выдавать их за независимые выборки нельзя.
Разберите минимум 5 ошибок вручную: значения признаков, y, обе predictions,
тип ошибки, гипотеза и следующий эксперимент. Если ошибок меньше — разберите все
и несколько низкоуверенных/пограничных случаев, не фабрикуйте ошибки.

## Артефакты и собственная реализация

Реализуйте [starter.py](starter.py) `run_experiment(raw_csv, output, seed=23)`.
Это единственная новая граница `NotImplementedError` проекта. Вспомогательные
функции `prepare_records`, `make_evaluation`, `json_bytes`, `write_bundle` разрешено
использовать: они не выбирают за вас split, модели, выводы или эксперименты.
Реализацию runner и независимый повторный запуск проверяют на человеческой защите.
Допустим другой самостоятельно написанный entry point с тем же воспроизводимым
протоколом; сохраните его исходники и точную команду. Технический artifact gate
не вызывает `run_experiment` и не требует именно эту обёртку.
Из корня после реализации, например:

```powershell
uv run python -c "from pathlib import Path; from projects.external_tabular.starter import run_experiment; run_experiment(Path('generated-reports/wine-input/winequality-red.csv'), Path('projects/external_tabular/submission'))"
uv run python -m projects.external_tabular.protocol projects/external_tabular/submission
uv run pytest projects/external_tabular -q -rx
uv run python scripts/learn.py check ml-external-tabular
```

Путь входа вынесен из output, чтобы запись bundle могла требовать пустую папку.
Если сначала скачали CSV прямо в submission, переместите исходный CSV в свою
рабочую папку и создайте submission заново. Не перезаписывайте предыдущие запуски.

`manifest.json`: integer `schema_version=1`, `project_id="ml-external-tabular"`,
`evidence_kind="INDEPENDENT_EXTERNAL_RUN"`, `artifacts` → logical name →
`{"path": relative_portable_path, "sha256": lowercase_actual_digest}`.
Каждая ссылка обозначает отдельный локальный файл внутри submission;
absolute/Windows drive/`..`/symlink escape и неверные хэши отклоняются.
Утилита `write_bundle` считает hashes после записи переданных bytes.

| Logical artifact | Содержимое |
| --- | --- |
| `raw` | Неизменённый полный red CSV; допустима собственная копия исходных bytes |
| `source` | JSON provider=`UCI Wine Quality`, url=официальный CSV или ZIP, license=`CC-BY-4.0`, retrieved_at, permission_note с attribution |
| `data` | Точный результат `prepare_records(raw_bytes)`; подменить признаки/labels отдельно от raw нельзя |
| `splits` | JSON с тремя непустыми упорядоченными массивами ID train/validation/test |
| `evaluation` | Результат `make_evaluation(data, splits, methods, "linear", "tree")`; methods → predictions и seconds; добавьте содержательные slices |
| `study` | Собственные решения и измерения, схема ниже |
| `repeat_1`, `repeat_2`, `repeat_3` | Отдельные результаты полного повторного fit; можно больше |
| `code` | Исходник собственного experiment; импортируемые изменённые файлы также добавляйте отдельными hash refs |
| `analysis` | Собственный русский analysis.md и короткая английская защита |

`study.json` содержит `configs={linear:{C: positive_number}, tree:{kind:"decision_tree",
max_depth: positive_int, min_samples_leaf: positive_int}}`. Для
`kind:"random_forest"` добавьте `n_estimators`; остальные настройки sklearn default,
`n_jobs=1` при replay. Baseline — most_frequent; scaler — StandardScaler, LR default
кроме C и random_state. Если нужен другой алгоритм/solver/feature transform,
расширьте проверяемый replay contract отдельным адаптером. Также `study.json` содержит непустые `feature_availability`, `leakage_audit`,
`split_rationale`, `selection_rule`, `error_analysis`, `limitations`,
`transfer_question`; `selection={used_split:"validation", selected_method:"linear"|"tree"}`;
`code_revision`=40-символьный Git SHA, `versions={python,numpy,sklearn}`,
целочисленный seed и `repeated_runs=[{seed, artifact:"repeat_1"}, ...]`.
У каждого повторного artifact: seed, row_ids в точном порядке validation,
labels из data, methods с `linear` и `tree`, их predictions и metrics от
`classification_metrics`, непустой `training_log`. Дополнительно сохраните
train config, число fit/строк, длительность и источник логов. Структура текста
проверяется как минимальная полнота; смысл и подлинность логов оценивает ревьюер.

### Авторский пример, который можно выполнить сразу

```powershell
uv run python -m projects.external_tabular.demo --output generated-reports/external-tabular-author
uv run pytest projects/external_tabular/test_evidence.py -q
```

Пример создаёт **отдельные 80 синтетических** строк, train-only scaler,
Dummy/LogisticRegression/DecisionTree, сохранённые predictions, парный bootstrap
и slices. Он не делает download, не пишет learner submission и маркирует себя
`AUTHOR_FIXTURE_ONLY`. Даже идеальная toy accuracy не измеряет реальное качество вина.
Его 60/20/20 разделение по порядку нужно проследить руками, а затем объяснить,
почему порядок исходного UCI CSV не является валидной моделью времени.
`validate_bundle(..., author_fixture=True)` проверяет только пример;
**каталог использует `validate_submission`**, где этот режим недоступен.

## Зачёт, защита и перенос

До собственной submission один `test_submission.py` даёт xfail в health suite.
Strict check превращает отсутствие обязательных артефактов в неуспех; нельзя отмечать
проект завершённым по авторским unit tests. `VERIFIED` подтверждает hashes,
воспроизводимость raw→data, split/group-disjointness, predictions/labels/метрики,
slices и arithmetic uncertainty. Валидатор повторяет fit всех трёх моделей и сравнивает predictions с сохранёнными;
повторные seed-runs также replay на validation. Он не заверяет
подлинность URL/авторство и не доказывает, что test не просматривали во время разработки.
Gate закрепляет полученный с официального UCI endpoint red CSV: 84 199 bytes,
SHA-256 `4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e`
(получен 28.10.2026 UTC). Хэш — проверка идентичности snapshot, не цифровая подпись UCI.
Технический PASS проверяет сохранённые артефакты и model replay; реализация runner,
его самостоятельность и clean rerun относятся к защите. Ревьюер воспроизводит
выбранный entry point и оценивает историю решений.
Нужны **оба** результата: technical PASS и human review.

| Область | Слабое доказательство | Сильное доказательство |
| --- | --- | --- |
| Постановка | «Обучил classifier» | Момент доступности features, стоимость ошибок, ограничение бинаризации |
| Leakage/split | random split без проверки X | Manifest до обучения, feature-группы, ограничения batch/time, train-only preprocessing |
| Сравнение | Одна accuracy/лучший seed | Baseline, общий holdout, dev selection, сохранённые парные predictions и честный проигрыш |
| Неопределённость | CI называют стабильностью обучения | Различают conditional bootstrap, retraining variance и domain shift |
| Ошибки | Пара скриншотов | IDs, counts, две полезные slices, гипотезы и проверяемый следующий эксперимент |
| Воспроизведение | Notebook с потерянным state | Raw/code hashes, versions, seeds, clean rerun и объяснение расхождений |

На защите объясните один false positive, изменение macro-F1 при редком классе,
почему scaler нельзя fit до split, и что модель видела в каждом fit.
**Transfer task:** независимо получите white-wine файл, проверьте schema/license,
сначала примените замороженный red model без настройки и измерьте shift; затем
спроектируйте новый train/dev/final split для адаптации. Не смешивайте эту проверку
с исходным red test. Другая задача — заменить target на порядковый/regression и
обосновать новую метрику. Ревьюер выбирает незнакомое изменение и просит выполнить
его без копирования вывода из авторского примера.

Следующий шаг — [внешнее исследование pretrained текста](../document_intelligence_lab/external_model_study/README.md),
затем доставка сохранённой модели через Document Intelligence service. Полезная
вакансионная формулировка результата: вы умеете строить честный эксперимент на
внешних данных, а не просто запускать sklearn.
