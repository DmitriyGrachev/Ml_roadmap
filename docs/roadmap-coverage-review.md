# Покрытие roadmap: пять направлений после первой волны

Фактическое продолжение: [Wave 2 — покрытие](wave2-coverage.md),
[проверки материалов, TODO и NOT_RUN](wave2-verification.md). Ниже сохранён исходный аудит.

Дата аудита: 26.09.2026. Проверено фактическое содержимое README, примеров,
student starters и тестов в текущей рабочей ветке `codex/ai-ml-wave1`.
**Первая волна завершена в согласованном объёме; этот аудит её не переоткрывает.**
Её результаты остаются в [отчёте проверки](wave1-verification.md).

Ниже «покрыто» означает наличие материала/контракта, а не прохождение учеником.
Все пять предложенных расширений имеют статус **PLANNED**: реализации, новых
тестов и зачётов пока нет. Это точечные продолжения существующих уроков,
не второй курс и не новая обязательная преграда перед первыми лабораторными.

## 1. Табличное ML

**Уже покрыто.** [Models](../modules/04_machine_learning/04_models/README.md)
объясняет Ridge, logistic regression, деревья, одинаковые folds и `GridSearchCV`.
[Пример](../modules/04_machine_learning/04_models/example.py) действительно
подбирает глубину дерева классификации на development folds и отдельно оценивает test.
[Model comparison](../modules/04_machine_learning/04_models/exercises/model_comparison/README.md)
— тестируемое задание с ровно тремя регрессорами: Dummy, Ridge и DecisionTree,
fold-level MAE, pipeline без leakage и фиксированным порядком folds.
[Preprocessing](../modules/04_machine_learning/03_preprocessing/README.md) и
[mixed feature pipeline](../modules/04_machine_learning/03_preprocessing/exercises/mixed_feature_pipeline/README.md)
дают imputation, scaling, one-hot и ColumnTransformer;
[Pandas](../modules/03_data_foundations/02_pandas_core/README.md) — группировки и join.

**Конкретный пробел.** Нет практики bagging/ансамблей и boosting; преобразование
типов/пропусков уже есть, но нет обоснованного создания нового признака с ablation.
Подбор параметров показан на глубине дерева, но не связан с ограниченным сравнением
семейств моделей. Существующий контракт `compare_regressors` расширять нельзя:
он намеренно требует ровно три кандидата.

**Одно задание — PLANNED: «Стоит ли усложнять прогноз длительности велопоездки?»**
Продолжить существующий regression case отдельным экспериментом: сохранить три
baseline-кандидата, добавить RandomForestRegressor и **один** boosting —
HistGradientBoostingRegressor из уже имеющегося scikit-learn. Повторно писать
линейный/tree baseline не требуется. Для всех кандидатов и вариантов признаков
нового эксперимента заранее сохранить одни и те же folds; старый контракт и его
настройки по умолчанию не менять. Сравнить исходные признаки с одним новым,
доступным до поездки, например отношением
набора высоты к расстоянию с явным правилом нулевого знаменателя. Любые обучаемые
преобразования остаются внутри pipeline. Заранее ограничить поиск, например
12 конфигурациями суммарно для новых моделей и тремя folds; test не участвует
в выборе модели, признака или параметров.

**Артефакт и критерий освоения.** Один отчёт содержит split IDs, параметры, MAE
каждого fold, разброс, сравнение с/без нового признака, время поиска и один финальный
test-результат замороженного выбора. Ученик объясняет bagging против boosting,
допустимость признака и оправданность сложности. Ансамбль не обязан победить.

**Место.** После Module 04 lessons 02–04 и самостоятельных `mixed_feature_pipeline`
и `model_comparison`; до более глубоких модельных экспериментов. NumPy, regression,
split и metrics заново не преподаются. Новые ML-библиотеки не нужны.

## 2. Calibration, thresholds, error analysis и интерпретация

**Уже покрыто.** [Evaluation](../modules/04_machine_learning/05_evaluation/README.md)
разделяет качество вероятностей и решений, threshold и метрики по срезам;
его [пример](../modules/04_machine_learning/05_evaluation/example.py) — MAE/RMSE
и ошибки регрессии по типу маршрута, не обучение calibrator.
[Threshold policy](../modules/04_machine_learning/exercises/threshold_policy/README.md)
задаёт проверяемый выбор порога по validation scores.
[Evaluation report](../modules/04_machine_learning/06_reproducibility/exercises/evaluation_report/README.md)
считает Brier, confusion-derived metrics и поддержку срезов из готовых вероятностей.
[Протокол эксперимента](experiment-protocol.md) упоминает reliability diagram,
log loss и ограничения малых выборок, но не даёт готовую calibration-практику.

**Конкретный пробел.** Нет fit/comparison calibrator и reliability bins/diagram;
threshold и отчёт существуют отдельно от обучения модели. Error analysis в основном
агрегирует срезы, а базовая интерпретация через признаки не закреплена заданием.
Brier сам по себе не равен процедуре калибровки.

**Одно задание — PLANNED: «Вероятность потребности растения в поливе и решение»**.
На локальном нейтральном classification case использовать существующий sklearn
classifier: сравнить исходные вероятности и sigmoid calibration. Модель и calibrator
обучать только на train, с внутренними folds; отдельный validation использовать
для выбора варианта и порога через уже реализованную учеником `choose_threshold`.
После фиксации решения один раз оценить test существующим evaluation-report контрактом.
Дополнить тот же отчёт таблицей reliability bins (диаграмма необязательна),
Brier/log loss, разбором нескольких
FP/FN и permutation importance на validation. Не менять признаки по финальному test.

**Артефакт и критерий освоения.** В одном отчёте видны роли train/calibration folds/
validation/test, число наблюдений в bins и срезах, выбранный порог и ошибки.
Ученик отличает ranking, calibration и thresholded decision; объясняет, почему
важность признака не доказывает причинность и как коррелированные признаки мешают
интерпретации. Нет требования, чтобы calibration непременно улучшила результат.

**Место.** После Module 04 lessons 05–06, `threshold_policy` и `evaluation_report`;
до итогового выбора модели для сервиса. Не требует завершённого boosting-задания.
Используется имеющийся scikit-learn, без обязательного SHAP или нового framework.

## 3. Transformers, диагностика и возобновление обучения

**Уже покрыто.** [Мост](../modules/04_machine_learning/07_training_bridge/README.md)
связывает loss, gradient и autograd.
[PyTorch lab](../labs/01_pytorch_foundations/README.md) охватывает полный lifecycle,
формы/dtype/device, zero_grad, train/eval, NaN и маленькую подвыборку.
Её [тесты](../labs/01_pytorch_foundations/test_starter.py) проверяют восстановление
весов, learning rate и momentum optimizer, а также возможность сделать следующий шаг.
[HF lab](../labs/02_huggingface_models/README.md) объясняет tokenization/masks,
self-attention, позиции, encoder/causal decoder и отличие classifier от language model;
есть loss history, частичная адаптация BERT и локальная загрузка safetensors/tokenizer.
[HF tests](../labs/02_huggingface_models/test_starter.py) наблюдают freezing,
режимы/градиенты и совпадение logits после reload.

**Конкретный пробел.** Внутренние формы attention пока в основном объясняются
словами; нет связанного диагностического отчёта по loss/gradient norms.
Восстановление optimizer и inference после reload **не доказывают продолжение
прерванной траектории обучения**. Нет задания со step/epoch, порядком minibatches,
RNG/sampler state и сравнением непрерывного и возобновлённого запуска.
Checkpoint workflow в Module 07 также не заменяет training checkpoint.

**Одно задание — PLANNED: «Прерванное обучение маленького encoder»**.
Переиспользовать локальный random BERT и синтетические тексты HF lab, без загрузок.
Зафиксировать формы token/attention tensors, роль padding/positions и журнал loss
и gradient norm; диагностировать один контролируемый сбой обучения.
Затем сравнить N шагов без остановки с остановкой после minibatch k и продолжением
в новом процессе. Для узкого CPU-сценария использовать `num_workers=0`, фиксированные
версии и данные. Сохранять модель, AdamW state, global step/epoch, порядок и позицию
sampler, состояния используемых Python/NumPy/Torch RNG, config и dataset/split identity;
scheduler state — только если scheduler используется. Resume не должен заново
сбрасывать optimizer или повторять уже обработанный minibatch.

**Артефакт и критерий освоения.** Две трассы sample IDs/loss, checkpoint и собственное
объяснение сбоя. В зафиксированной CPU-среде совпадают порядок оставшихся примеров,
число шагов и состояния optimizer/весов с заранее указанной численной погрешностью.
Ученик объясняет, почему одних весов и seed недостаточно. Это не обещание побитового
совпадения разных устройств/версий и не требование реализовать transformer с нуля.

**Место.** После самостоятельных PyTorch и HF labs, перед PLANNED SFT/PEFT.
Это новое продолжение, а не недоделка согласованной первой волны; достаточно
существующей группы `training`.

## 4. Memory-aware data pipelines, streaming и данные

**Уже покрыто.** [Generators](../modules/01_python_core/07_iterators_generators/README.md),
[NDJSON stream](../modules/01_python_core/07_iterators_generators/exercises/stream_transactions/README.md)
и [paged stream](../modules/01_python_core/exercises/paged_stream/README.md)
имеют контракты и тесты ленивого чтения без prefetch.
[Data quality](../modules/03_data_foundations/03_data_quality/exercises/quality_report/README.md)
валидирует уже переданный DataFrame, не поток произвольного размера.
[Banking domain](../projects/banking_ai_lab/banking_ai_lab/domain.py) задаёт схему,
но контракт importer возвращает все строки/ошибки и не обещает ограниченную память.
[Протокол](experiment-protocol.md) и [HF lab](../labs/02_huggingface_models/README.md)
уже требуют происхождение/лицензию, snapshot/hash, split IDs, versioned preprocessing,
правила разметки, конфликтующие/неоднозначные метки и исключение утечки признаков.

**Конкретный пробел.** Нет единой проверяемой цепочки «поток → схема/разметка →
ограниченный batch → сохранённый data release». Ленивая функция не делает весь
pipeline memory-aware: [HF runner](../labs/02_huggingface_models/run.py) намеренно
материализует небольшой CSV целиком через `list(DictReader(...))`, затем создаёт
Dataset/списки. Это допустимый малый опыт первой волны, не streaming-практика.
Нет сквозного измерения буферов/памяти, проверки изменения схемы и неполного output.

**Одно задание — PLANNED: «Потоковый выпуск локального каталога обращений»**.
Читать локальный CSV/JSONL с версией схемы, ограничением размера записи и rubric
разметки фиксированными страницами через самостоятельно реализованный `iter_pages`.
Переиспользовать правила data-quality, но писать принятые строки и причины отклонения
постепенно, не собирать все результаты/ошибки в список. Неоднозначную метку отправлять
на review. Сохранить source checksum, origin/license, schema/rubric versions, стабильные
ID, counts и checksums выходов в manifest; публиковать manifest только после завершения.
Повторный запуск в новую папку воспроизводит выпуск, а конфликтующий существующий
output не дополняется молча. В этом узком задании ID можно связать с source hash и
позицией строки; **глобальную content-deduplication не заявлять** без отдельного
disk-backed индекса или доказанной границы размера множества ключей.

**Артефакт и критерий освоения.** Один data release и короткий resource report:
инструментированное чтение без prefetch, размер страницы не более B и суммарно
не более заранее заявленного c×B записей во всех буферах при фиксированном c,
плюс фиксированное служебное состояние; измерение Python-allocations с оговоркой,
что это не весь RSS/native memory. При увеличении N и фиксированном B результаты
не накапливаются в памяти. Неверная схема обрабатывается явно, спорные метки имеют
причину, перезапуск даёт те же bytes/hashes без повторного append. Частичный выпуск
не принимается за готовый. Для этой учебной цепочки достаточно stdlib и имеющегося
стека; Spark/Airflow/Parquet не являются prerequisite.

**Место.** После Python I/O/generators/testing и Module 03 data-quality; до перехода
к большим наборам в HF/real RAG/tracking. Не блокирует существующие маленькие labs.

## 5. AI/ML system design и оправданная сложность

**Уже покрыто.** [Problem framing](../modules/04_machine_learning/01_problem_framing/README.md)
задаёт объект/момент предсказания и baseline; [протокол](experiment-protocol.md)
прямо допускает правила/SQL вместо AI и различает retrieval и fine-tuning.
[LLM evaluation](../modules/05_llm_engineering/05_evaluation/README.md) связывает
quality, latency и cost. [Module 08](../modules/08_production_ai/README.md) даёт
serving identity/readiness, release gates, observability, budgets, privacy и rollback,
с тестируемыми локальными policy exercises. [Будущий Document Intelligence Lab](../projects/document_intelligence_lab/README.md)
уже предусматривает architecture note и защиту trade-offs, но пока PLANNED.

**Конкретный пробел.** Материал распределён по урокам; нет одной ограниченной
практики с явными входными требованиями, альтернативами, измеримыми ограничениями,
отказом от ненужных компонентов и защитой решения при изменении условий.
Локальные policy tests не проверяют реальный deploy, нагрузку или доступность.

**Одно задание — PLANNED: «Защита архитектуры маршрутизации обращений библиотеки»**.
Подготовить один decision brief на основе уже полученных учеником результатов:
сравнить правила, classical ML, pretrained encoder и обоснованно принять/отклонить
RAG/fine-tuning/agent workflow. Указать online против batch, данные и permissions,
качество/цену ошибки, latency/ресурсный бюджет, fallback при недоступной модели,
versioned preprocessing, monitoring и восстановление. Числа разделять на измерения,
заданные требования и непроверенные оценки. Не строить все альтернативы и не
разворачивать инфраструктуру ради записки.

**Артефакт и критерий освоения.** Один ADR/architecture note со схемой потока,
таблицей альтернатив и кратким runbook, переиспользующим Module 08. Есть хотя бы
один явно отвергнутый избыточный компонент; для решения «AI не нужен» указаны
проверяемые основания. На защите ученик пересматривает выбор для двух сценариев:
недоступная модель и изменившиеся данные/нагрузка; называет критерии перехода к
более сложной системе и честные пробелы измерений. Реальный production readiness
не засчитывается по текстовому ADR или симуляции.

**Место.** Первичная постановка остаётся в Module 04 lesson 01. Эта цельная защита —
после ML/HF evaluation и соответствующих уроков Modules 05/08, перед расширением
Document Intelligence/serving/lifecycle. Новые сервисы и зависимости не нужны.

## Как встроить без дублирования

По prerequisites расширение 4 возможно раньше остальных: Python/data foundations →
потоковый выпуск. Расширение 1 продолжает model selection; 2 — evaluation; 3 —
PyTorch/HF; 5 собирает выбор подхода и эксплуатацию. Это точки следующего развития,
а не требование пройти все пять перед первым обучением модели.

Сейчас изменена только документация. Новые IDs не добавлены в curriculum,
папки упражнений не созданы, контракты старых заданий не расширены, зависимости и
progress не изменены. При будущей реализации нужны отдельные acceptance tests
и фактические результаты; ни один PLANNED-пункт пока не имеет зачёта.
