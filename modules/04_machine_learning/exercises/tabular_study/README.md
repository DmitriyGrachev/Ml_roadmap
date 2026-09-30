# Самостоятельное табличное исследование

ID: `ml-tabular-study` · материалы **READY** · CPU, offline.
Реализация ученика TODO; его эксперимент NOT_RUN; защита REQUIRES_REVIEW.

Вход — небольшие синтетические обращения в поддержку. `outcome` обозначает нейтральный
двоичный результат процесса, а не качество человека или кредитный риск. Цель — защитить
выбор модели и решения при ограниченном бюджете, сохранив проверяемые свидетельства.
Нет обязательного победителя и минимального accuracy. Маленький fixture не обосновывает
применение модели к реальным людям или реальной службе поддержки.

## Prerequisites и границы

Сначала завершите [ml-model-comparison](../../04_models/exercises/model_comparison/README.md),
[ml-mixed-feature-pipeline](../../03_preprocessing/exercises/mixed_feature_pipeline/README.md),
[ml-threshold-policy](../threshold_policy/README.md),
[ml-evaluation-report](../../06_reproducibility/exercises/evaluation_report/README.md),
[data-paired-model-comparison](../../../03_data_foundations/exercises/paired_model_comparison/README.md).
Для групп используйте [split_sensor_groups](../../02_validation/exercises/group_safe_split/README.md),
для интерпретации — [ml-evaluation](../../05_evaluation/README.md).

Редактируйте `starter.py` и собственные вспомогательные файлы этого упражнения.
`run_experiment(data_path: Path, output_dir: Path, *, seed: int) -> Path` остаётся TODO:
создаёт **новый** output_dir и возвращает `output_dir / "manifest.json"`.
Существующий output_dir должен вызвать `FileExistsError`, сохранив все файлы.
Входной `data_path` остаётся побайтно неизменным; `dataset.csv` — точная копия его
bytes, включая порядок строк, заголовки и формат. Преобразования выполняются в pipeline,
а не перезаписью snapshot. Проверка фиксирует input до вызова и сверяет обе копии.
Output должен быть свежим обычным каталогом: перенаправления symlink/junction и
выход `model.pkl` за заранее зафиксированный каталог не получают автоматического доверия.
Не меняйте старый `compare_regressors`, tests, fixture или validator ради зачёта.
Подключайте освоенные границы через `importlib.import_module`, например
`modules.04_machine_learning.exercises.threshold_policy.starter` (`choose_threshold`).
Аналогично используйте `build_evaluation_report` и `paired_difference` из prerequisites;
не копируйте их алгоритмы в новый starter. Регрессионный pipeline из prerequisites
показывает контракт преобразований; для классификации вы самостоятельно выбираете estimator.

## Данные и вопросы до обучения

`make_fixture(seed: int) -> pd.DataFrame` возвращает 144 строки / 48 групп, без сети.
`row_id` уникален; `group_id` объединяет повторные обращения; `time_id` — момент входа.
При прогнозе известны `message_length` (есть пропуски), `prior_contacts`, `queue_minutes`
и `channel`. `outcome` доступен позже. ID и outcome не являются признаками.
Самостоятельно исследуйте пропуски, баланс, повторения, диапазоны и размер групп.
Объясните, оцениваете ли новые аккаунты или будущее; групповые folds этого контракта
оценивают новые аккаунты. Для будущего нужна отдельная временная схема, а не обещание
«утечки нет» на основании одного group split. Не смотрите test при EDA для выбора решений.

До поиска сохраните непересекающиеся development/test группы и ровно три folds внутри
development: каждый fold делит development на train/validation, группы не пересекаются,
каждая строка один раз попадает в validation. Используйте одинаковые folds для всех моделей.
Выберите primary metric и цену FP/FN, пороговую политику и временной бюджет заранее.

Обязательные семейства: DummyClassifier, LogisticRegression, DecisionTreeClassifier
или RandomForestClassifier, HistGradientBoostingClassifier — один sklearn boosting.
Обсудите L2 и масштабирование. Fit imputation/encoding/scaling и других обучаемых
преобразований выполняйте только на train fold. Добавьте один осмысленный признак,
известный при прогнозе, и ablation с ним/без него при прочих равных настройках.
Храните вычисление нового признака внутри сериализуемого pipeline, чтобы replay получал
те же исходные колонки. Запишите обоснование доступности признака без target leakage.

Максимум **12 candidate configurations × 3 development folds**, включая baseline,
варианты feature set и calibration. Повторные запуски и время учитывайте отдельно,
не прячьте их в лимите; запишите внутренние fit calibration и их стоимость.
Сравните исходный и sigmoid-calibrated вариант: calibrator обучается внутри train fold,
не на внешнем validation и не на test. Выбор calibration, feature, модели и threshold —
по development; threshold выбирает ваш `choose_threshold`. Test открывается один раз
после заморозки. Повторное inference для проверки сохранённых bytes — проверка воспроизводимости,
а не разрешение повторно выбирать модель по test.

## Мини-практика ансамблей

Прочитайте [продолжение models lesson](../../04_models/README.md#короткое-продолжение-bagging-random-forest-и-boosting)
после прежних основ деревьев и validation. Команда sensor example ниже теперь также
печатает `compare_sensor_ensembles(seed=11)`: сравните `probabilities`,
`forest_disagreement`, `forest_average_error` и последовательность
`boosting_validation_brier`. Почти нулевой average error проверяет усреднение
вероятностей леса; ненулевой disagreement показывает, что деревья различаются.
Восемь последовательных Brier — наблюдение за boosting, а не восемь независимых лесов.

**Самостоятельная вариация обязательна даже при выборе одного дерева в большом study.**
В своём вспомогательном файле на тех же sensor train/validation данных обучите RF
с `max_features=1` и `max_features=None`, сохранив seed, восемь деревьев и глубину.
Сравните разброс вероятностей отдельных деревьев и validation Brier среднего.
Затем сравните boosting с `learning_rate=0.05` и `0.2` при тех же восьми шагах,
сохранив Brier каждого шага. Меняйте один фактор за раз; не используйте test поддержки.
Это четыре малых учебных fit вне бюджета большого support study; укажите их отдельно.

**Критерий и защита:** покажите свои массивы/таблицу и объясните, какие выборки
получает каждое дерево RF, где выбираются признаки, почему лес усредняет вероятности
и почему очередной boosting learner зависит от предыдущих. Объясните наблюдаемые
изменения и отсутствие гарантированного победителя. Результат не обязан улучшиться.
Unit test примера подтверждает вычисления демонстрации; вашу вариацию и объяснение
проверяет человек (`REQUIRES_REVIEW`). Full study по-прежнему допускает дерево **или** RF.

## Свидетельства schema 1

`evidence.py` читает файлы и сверяет результаты, но не пишет отчёт за вас. JSON использует
неокруглённые конечные числа и UTF-8. Порядок prediction rows совпадает с сохранёнными ID.
SHA-256 — lowercase digest фактических bytes. Схема задаёт файлы, не архитектуру pipeline.

| Файл | Контракт |
| --- | --- |
| `dataset.csv` | Сохранённый исходный snapshot со всеми входными колонками и outcome; строковые IDs |
| `split.json` | `development_ids`, `test_ids`, `folds`: три объекта `train_ids`, `validation_ids` |
| `config.json` | `seed`, `features` (исходные input columns), `threshold`, `selected_id`, `candidates`, `reruns`, `elapsed_seconds`; добавьте metric/policy, параметры и внутренний fit budget |
| `model.pkl` | pickle объекта `{"identity": identity, "model": fitted_pipeline}`; Pipeline поддерживает predict/predict_proba, classes_ равен [0, 1] |
| `predictions.json` | `identity`, `rows`: `row_id`, `label`, `probability` класса 1, исходный `prediction` модели, `decision = probability >= threshold` |
| `study.json` | Обязательные development/calibration/ablation/importance/paired/report результаты, описанные ниже |
| `paired/` | Артефакты schema 1 из data-paired-model-comparison на development OOF predictions |
| `manifest.json` | Идентичность, hashes, metrics и review, описанные ниже |

`identity` содержит `dataset_sha256`, `split_sha256`, `config_sha256`.
Каждый candidate имеет уникальный строковый `id`, `family` из
`Dummy`, `LogisticRegression`, `TreeOrRandomForest`, `HistGradientBoostingClassifier`,
`calibration` (`raw`/`sigmoid`), `feature_set` и все параметры обучения.
Все четыре family обязательны, `selected_id` ссылается на один candidate.
Raw/sigmoid пара отличается только `id`/`calibration`; ablation пара — только
`id`/`feature_set`. Это позволяет сравнивать именно заявленное изменение.

`study.json` обязателен; произвольные флажки «готово» не заменяют результаты:

- `runs`: по одной записи на candidate × fold. Поля `config_id`, `fold_id` (0, 1, 2),
  `predictions` (объекты `row_id`, `probability` для validation в сохранённом порядке),
  `brier`, `log_loss`. Числа пересчитываются из сохранённых validation predictions.
- `calibration`: `raw`, `sigmoid` — IDs соответствующих runs; `reliability` содержит
  ключи raw/sigmoid с bins/counts OOF probabilities всего development в формате двух bins
  из manifest. Они пересчитываются. Дополнительно исследуйте более подробные bins;
  оценивайте Brier и log loss, не только accuracy.
- `ablation`: `with_feature`, `without_feature` — IDs, `feature`, `availability` — объяснение.
- `permutation_importance`: `config_id`, `fold_id`, `feature`, `predictions` после
  перестановки **validation** признака, `brier_increase` относительно исходного run.
  Сохраните seed/перестановку и повторы как дополнительные данные; один массив — минимум
  для механической проверки разницы. Связанные признаки могут делить важность;
  перестановка не доказывает причинность и может создавать нереалистичные комбинации.
- `paired_comparison`: `config_a`, `config_b`. Соберите OOF вероятности по development IDs;
  `paired/` использует outcome как label, group_id как unit_id, `squared_error` как loss.
  Повторные строки одной группы образуют одну независимую единицу. Весь Task 2 validator
  вызывается повторно и связывает оба массива с конкретными development runs.
  Интервал условен на уже сохранённые predictions: перекрывающиеся train folds и выбор
  конфигураций могут делать его оптимистичным; это не независимый повтор всего обучения.
- `evaluation_report`: полный результат вашего `build_evaluation_report` на frozen test,
  с `model_name = selected_id`, slices по channel. Overall и slice metrics сверяются.

Manifest: `schema_version=1`, `exercise_id="ml-tabular-study"`, identity, `config`
(точная копия config.json), `model_sha256`, `predictions_sha256`, `study_sha256`,
`paired_sha256` (hash `paired/manifest.json`). Также `versions` (минимум python/sklearn),
`code`: revision, dirty (bool), diff_sha256 (включите собственные новые файлы в снимок кода),
и `analysis`: status=`REQUIRES_REVIEW`, содержательные `comparison`, `conclusion`.
Поясните отличие моделей, интервалы неопределённости, ошибки, ограничения и выбор.

`metrics` в manifest: `count`, `accuracy` решений при threshold, `brier`, `log_loss`,
`fp`, `fn`; `slices` — по каждому channel объекты count/fp/fn; `reliability` — две записи
для [0, 0.5) и [0.5, 1], каждая с lower/upper/count/mean_probability/positive_rate.
Для пустого bin средние равны null. Это минимальный формат replay; для анализа сохраните
более подробные bins в study. Указанные числа сверяются с реальным test inference.
Ни CSV, ни JSON, ни hash не доказывают честность происхождения данных или обучения.

## Доверие и запуск (Windows / PyCharm)

Pickle выполняет Python-код при загрузке. **Checksum не делает pickle безопасным.**
Не передавайте модели из fixtures, downloads, чужих каталогов или неизвестного источника.
Разрешение даёт только явный `trusted_model_path` к **своему** локально созданному model.pkl,
после проверки происхождения. Путь абсолютный и должен совпасть с artifact внутри root.
Manifest не может сам разрешить загрузку. `validate_evidence(root)` без разрешения
завершается ошибкой, а не частичным «успехом». Полный интерфейс:
`validate_evidence(root: Path, *, trusted_model_path: Path | None = None) -> None`.
После replay происхождение, интерпретация и защита всё ещё `REQUIRES_REVIEW`.

Из корня репозитория, новый временный каталог для каждого примера:

```powershell
$studyTemp = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $studyTemp
.venv/Scripts/python.exe -m modules.04_machine_learning.exercises.tabular_study.fixture "$studyTemp/support.csv" --seed 23
.venv/Scripts/python.exe -m modules.04_machine_learning.exercises.tabular_study.example "$studyTemp/sensor" --seed 11
.venv/Scripts/python.exe scripts/learn.py test ml-tabular-study
.venv/Scripts/python.exe scripts/learn.py check ml-tabular-study
```

В PyCharm вызовите `run_experiment` из starter с support.csv и новым study output path.
После собственной реализации и только для собственного model.pkl:

```powershell
.venv/Scripts/python.exe -m modules.04_machine_learning.exercises.tabular_study.evidence "$studyTemp/study" --trust-local-model "$studyTemp/study/model.pkl"
```

Sensor lifecycle обучает одну модель обслуживания датчиков, сохраняет и повторно
загружает **созданный им самим** объект. Отдельная ensemble-демонстрация выше сравнивает
механику трёх моделей. Lifecycle не выбирает порог,
не калибрует поддержку и не создаёт учебный отчёт. Автоматические evidence fixtures
создают собственный estimator в tmp_path и искусственные, проверяемые вручную массивы;
они проверяют validator, а не заменяют проведённое исследование.

## Подсказки и критерий

1. Сначала сформулируйте unit of analysis, заморозьте folds и сохраните их до fit.
2. Затем составьте таблицу конфигураций с одинаковыми folds и ограничением бюджета.
3. После development решений заморозьте pipeline/calibrator/threshold; сохраните test inference.
4. Проверьте связь каждого числа с исходными строками, а каждого решения — с validation.

Unit tests проверяют контракт/отказ при порче; CPU smoke проверяет сериализацию и настоящее
inference. `test ID` допускает ожидаемые xfail незавершённого starter; `check ID` запускает
все три собственных test-файла без допуска xfail/skip и падает на TODO. Проверка не создаёт
учебные результаты в постоянных каталогах. Отдельный evidence CLI читает ваши saved outputs.

ML evaluation — реальные сравнительные результаты learner. На защите объясните L2,
train-only preprocessing/calibration, leakage, выбор metric/threshold, доступность feature,
ablation, reliability, FP/FN slices, важность и неопределённость разницы моделей.
Заявления о train chronology, отсутствии скрытого test reuse, качестве постановки и
причинности невозможно доказать согласованным JSON: они остаются **REQUIRES_REVIEW**.
Зелёный check подтверждает автоматические контракты, но не заменяет эту защиту.
