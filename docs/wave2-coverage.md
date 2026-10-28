# Wave 2: фактическое покрытие и недублирующие расширения

## Актуальное дополнение после сверки книги — 28.10.2026

Пользователь подтвердил первый локальный generator через существующие Ollama и
Qwen2.5 и отдельно напомнил о пробелах объяснения/практики. Это две линии работы:
[короткий дизайн Windows-опыта](superpowers/specs/2026-10-28-local-generator-design.md)
не закрывает учебные дополнения ниже. Адаптер и первый lexical+LLM smoke
[проверены](local-generator-verification.md); dense+LLM и ML evaluation ещё NOT_RUN.
Старые исторические статусы ниже не переписываются.

<a id="coverage-gaps-20261028"></a>

### Пять пробелов: учебные материалы подготовлены 28.10.2026

Это расширение существующих уроков, не новый курс. Номера ниже — строки карты,
не новые lesson IDs. Добавлены пять отдельных exercise targets; старые targets и
learner progress сохранены. READY ниже относится к материалам, не к освоению.
Материалы: русский текст + English terms, интуиция → точное объяснение → разобранный
пример → типичная ошибка → самостоятельная вариация. Визуальные опоры должны
совпадать с запускаемым кодом; student TODO и собственные выводы не заполняются.

| Пробел / статус | Что переиспользовать | Чего ещё не хватает / визуальная опора | Самостоятельная проверка и критерий результата | Место |
| --- | --- | --- | --- | --- |
| 1. Вход в Python — READY | [Environment](../modules/01_python_core/00_environment/README.md) → прежние Object Model/Collections/Functions | [Последовательный разбор](../modules/01_python_core/00_environment/basics.md): expressions/indentation/if/for/range/while/def/return/import; trace-таблицы и [демо](../modules/01_python_core/00_environment/basics_demo.py) | [`python-control-flow`](../modules/01_python_core/00_environment/practice/README.md): новый счётчик подписей, ordinary/empty/invalid/boundary tests; объяснить накопление и return | После Environment перед Object Model; далее прежний порядок |
| 2. Дизайн эксперимента — READY | Прежние statistics/Bayes, [paired comparison](../modules/03_data_foundations/exercises/paired_model_comparison/README.md), [randomized experiment](../modules/03_data_foundations/exercises/randomized_experiment/README.md) | [Hypothesis/p-value, Type I/II, MDE/power/n, multiplicity/peeking](../modules/03_data_foundations/04_practical_statistics/experiment_design.md), формулы/таблицы и bounded known-sigma simulation | [`data-experiment-design`](../modules/03_data_foundations/exercises/experiment_design/README.md): Bonferroni TODO + собственный prereg experiment; unit отдельно от stochastic smoke и защиты REVIEW | После probability/Bayes, validation/evaluation и paired/randomized prerequisites |
| 3. Представления и необычные данные — READY | Прежние [preprocessing](../modules/04_machine_learning/03_preprocessing/README.md), models, tabular study | [KMeans/PCA/IsolationForest](../modules/04_machine_learning/04_models/representations.md), численное сравнение расстояний до/после scale, формы и frozen train boundary | [`ml-representation-study`](../modules/04_machine_learning/exercises/representation_study/README.md): inverse-map TODO + свой sensor experiment; объяснить cluster≠class, anomaly≠bad data | После NumPy/preprocessing/validation/models. SVM/NB — OPTIONAL, не расширяются этой работой |
| 4. Fairness и bias — READY | Прежние data quality, [evaluation](../modules/04_machine_learning/05_evaluation/README.md), threshold/calibration | [Selection/measurement/label bias, denominators/uncertainty, конфликт критериев](../modules/04_machine_learning/05_evaluation/bias.md); confusion tables + [SVG](../modules/04_machine_learning/05_evaluation/bias_composition.svg) до/после sampling | [`ml-bias-slices`](../modules/04_machine_learning/exercises/bias_slices/README.md): grouped counts/rates TODO + своё исследование; пустой denominator=None; причинные выводы и решение требуют REVIEW | После metrics/threshold/calibration, до объявления системы пригодной |
| 5. SQL + container — MATERIALS READY; external runtime NOT_RUN | Прежние PostgreSQL/analytics SQL и [CPU service](../projects/document_intelligence_lab/service/README.md) | [SELECT/NULL/group/join/window с таблицами](../modules/02_python_backend/07_postgresql/sql_basics.md) + [image/container/mount/restart практикум](../modules/02_python_backend/09_docker_delivery/container_practice.md) | [`backend-sql-foundations`](../modules/02_python_backend/exercises/sql_foundations/README.md): latest-valid query TODO; SQLite unit не доказывает PostgreSQL. Container done только после настоящего build/HTTP/restart/recreate/recovery | SQL после Python/data; container после backend/CPU API. Docker/WSL/PostgreSQL не устанавливались |

Новые executable IDs добавлять лишь при отдельном новом проверяемом умении и после
определения контракта, не ради количества. Человеческое объяснение/своя защита остаются
REQUIRES_REVIEW даже при зелёных tests. Материалы реализованы; ученические TODO,
эксперименты и отчёты не выполнены. [Проверки и порядок работы](five-gaps-verification.md).
Уточнение границ: короткий Python-вход прикрепить к Environment перед Object Model,
не переписывая сам пилот. В статистике не повторять уже существующие assignment,
агрегацию независимых единиц и fixed horizon: новый акцент — preregistration,
minimum detectable effect/power/sample size и последствия optional stopping.
vLLM, генеративное качество, pretrained adaptation и production deployment имеют
отдельные runtime gates; они не являются доказательством освоения пяти тем выше.

Текущий остаток после пакетов 1–7 и интеграционной приёмки сверен 11.10.2026:
[единый план R01–R12](superpowers/plans/2026-10-11-remaining-roadmap.md).
Из шести подтверждённых пробелов Python/backend три Python-пробела дополнены в
[R01](#remaining-r01); три backend-пробела дополнены в [R02](#remaining-r02).
Labs, CI/сервис и Document Intelligence — [дополнение R03–R11](#remaining-integration);
[R12](superpowers/plans/2026-10-11-remaining-roadmap.md#r12) содержит только варианты специализации.
Исторические PLANNED в ранних разделах ниже не повод переделывать готовую теорию.
Материалы R01/R02 — READY; остальные проверки разделены на local/offline и runtime.
Настоящие локальные MLflow/Qdrant/PEFT mechanics проверены в
[runtime-продолжении](local-runtime-continuation.md). MiniLM CLS retrieval теперь измерен
на фиксированном teacher corpus; остальные pretrained/GPU/cloud runs — NOT_RUN,
progress не менялся. Исторический аудит ниже сохранён как исходная точка.

<a id="remaining-r01"></a>

## Дополнение R01: точечные Python-механизмы, 11.10.2026

Не новый курс: три существующих урока получили недостающий разбор. Таблица
разделяет объяснение, наблюдаемую демонстрацию и работу, которую делает ученик.
READY относится к материалам, не к решению старых заданий или новой вариации.

| Механизм / прежний ID | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Value object / `python-data-modeling`, `python-payment-model` | [Конструктор, invariant, runtime-граница, finite/ASCII/frozen](../modules/01_python_core/05_data_modeling/theory.md) | [PageSpan и отдельные пробы](../modules/01_python_core/05_data_modeling/walkthrough.py), не Payment | Таблица допустимых границ, схема init → post_init → объект/ошибка | GridCell-вариация и прежний [payment_model](../modules/01_python_core/05_data_modeling/exercises/payment_model/README.md) | Прогноз до запуска, шесть вопросов; авторские value-object tests не заменяют перенос |
| Atomic I/O / `python-io`, `python-json-export` | [Фазы отказа, владение temp, cleanup и исходная ошибка](../modules/01_python_core/06_exceptions_io/theory.md) | [Отдельно notice publication и broken catalog serialization](../modules/01_python_core/06_exceptions_io/walkthrough.py), не общий JSON exporter | Таблица состояния writer/draft/старых bytes по фазам | Прогноз cleanup failure и прежний [json_export](../modules/01_python_core/06_exceptions_io/exercises/json_export/README.md) | Семь вопросов; реальные failure tests, пределы atomicity/durability |
| Test design / `python-testing`, `python-mock-provider` | [От договора к independent expected, parametrization и raises](../modules/01_python_core/09_testing/theory.md) | [Полный preview, девять teacher cases](../modules/01_python_core/09_testing/walkthrough.py) | Матрица ordinary/empty/invalid/boundary → ошибка, которую ловим | [Document outline: собственные tests + v2](../modules/01_python_core/09_testing/practice/document_outline/README.md), затем прежний mock_provider | Пустой файл тестов даёт exit 5; осмысленность выбора случаев — ручной review |
| Traceback/decomposition / `python-debug-mutable-defaults`, `python-review-stateful-report` | Тот же testing-разбор: первая неверная предпосылка и границы функций | [Реальные frames](../modules/01_python_core/09_testing/debugging/empty_preview/broken.py); независимая композиция paragraph counts | Таблица caller/вход/ответственность и промежуточные абзацы | Прежние debugging/review + дефектный кандидат outline без готового исправления | Контрпример, причина, перенос требования; семь общих вопросов testing, защита REQUIRES_REVIEW |

Вход — существующие Object Model/Functions/Typing и соответствующие уроки; место —
Python Core перед будущим A1. Новых exercise ID нет: outline — явно обозначенная
ручная практика, не скрытое дополнение старого `check`. Прежние TODO/контракты сохранены.
Техническое свидетельство и ограничения — [R01 verification](r01-verification.md).

<a id="remaining-r02"></a>

## Дополнение R02: backend и SQL, 11.10.2026

| Тема / прежний ID | Объяснение и разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- |
| Pydantic / `backend-transaction-contract` | [Parsing → after validator → service](../modules/02_python_backend/02_pydantic/theory.md), print batches вместо Transaction | Схема отказа и таблица input/type/loc | Датчик с диапазоном, затем прежний contract | Прогноз трёх запросов, причины 422, шесть вопросов; реальные route tests |
| SQLAlchemy / `backend-transaction-repository` | [SQLite session lifecycle](../modules/02_python_backend/06_sqlalchemy/theory.md), отдельные label batches | Состояния pending/flushed/committed и ветка rollback | Новая вариация batch, затем прежний repository | Предсказать persisted rows после UNIQUE failure; объяснить flush ≠ commit |
| API testing / `backend-api-test-review` | [Yield-fixture](../modules/02_python_backend/08_api_integration_testing/theory.md), shelf notes вместо student route | Setup → startup → yield → shutdown → teardown | Независимая вариация, затем прежний review | Проследить cleanup после failed test; не перепутать lifespan с HTTP-client closure |
| SQL / `backend-analytics-sql` | [Plan/index](../modules/02_python_backend/exercises/analytics_sql/plan_theory.md), parcel lookup | Scan/lookup, план до/после, измеренные warm durations | Другой фильтр/индекс с проверкой одинаковых строк | Отделить корректность, query plan, время и цену индекса |

Место — соответствующие backend/SQL уроки после Python prerequisites, перед переносом
модели в сервис. [16 тестов и остальные проверки](r02-verification.md) подтверждают
локальные механизмы. Задания/старые targets и progress не менялись; самостоятельное
освоение не объявляется по авторскому pytest.

<a id="remaining-integration"></a>

## Дополнение R03–R11: от учебного механизма к самостоятельной системе

Новые материалы дополняют существующий маршрут. Наличие runnable demo — не завершённый
учеником проект. Новая регистрация только одна: `document-a1-reproduction` (exercise,
два явных test target). Итого 163 материала; прежние 162 ID/targets/order и progress сохранены.

| Пакет | Объяснение / разобранный пример | Визуальная опора | Самостоятельная работа | Проверка и место |
| --- | --- | --- | --- | --- |
| R03 A1/CI | [A1](../projects/document_intelligence_lab/part_a1/README.md), [CI](continuous-integration.md): artifacts, reload и разные свидетельства | Split/manifest → model → predictions; confusion; ветви CI | [Другие документы и требования](../projects/document_intelligence_lab/part_a1/exercise/README.md) | Строгий отдельный `check`; после Data/ML. Hosted CI NOT_RUN |
| R04 service/tracking | [API](../projects/document_intelligence_lab/service/README.md), [tracking](../projects/document_intelligence_lab/tracking_intro/README.md) | Startup/ready, A→B→отказ→A; measured recovery SVG | Своя A1 модель, incident/report без готового ответа | ASGI/reload и actual local MLflow runs/flavors/replay проверены; container NOT_RUN; после A1/backend |
| R05 cloud | [Права, storage, budget и launch gate](../projects/document_intelligence_lab/deployment/README.md) | Request/service/artifacts и граница секретов | Выбрать provider/region/budget, заполнить launch card | AWAITING_CHOICE; deployment не выполнен |
| R06 encoder comparison | [Один cohort, три модели](../projects/document_intelligence_lab/part_a/README.md), [input preflight](../projects/document_intelligence_lab/part_a/preflight.py) | Data/split/labels → `[B,T]` → `[B,C]` → общий test; 3 pins → inventory/cohort gate | Свой pretrained experiment, разные группы ошибок; неверный pin без изменения оригинала | Local random-model parity и offline input gate; pretrained/device/budget execution NOT_RUN; после обеих labs |
| R07 retrieval/answer | [Real RAG](../labs/03_real_rag/README.md), [часть B](../projects/document_intelligence_lab/part_b/README.md) | Source→chunk→vector/index; ACL до top-k; две оси оценки | Разрешённый corpus, independent judgments и ответы | Actual MiniLM CLS на пяти queries измерен отдельно от Qdrant mechanics; generator/LLM quality NOT_RUN; после modules 05/06 |
| R08 vLLM | [Linux runtime и bounded client](../labs/05_model_serving/README.md) | Prefill/decode, KV shapes, очередь и TTFT timeline | Admission/cancellation вариация и реальный endpoint report | Offline transport tests; DEFERRED_ENV по решению пользователя 11.10.2026, Linux/GPU/vLLM NOT_RUN |
| R09 lifecycle | [Release, monitoring и recovery](../labs/06_ml_lifecycle/README.md), [coupled local разбор](../labs/06_ml_lifecycle/coupled-recovery.md), [registry](../projects/document_intelligence_lab/tracking_intro/registry-lifecycle.md) | Две ветки release, corpus/representation/index; A→B→A, distributions/labels | Incident/rollback на собственной модели; live ACL отдельно от historical snapshot | Actual coupled local restore/classifier/index/fresh-process PASS; registry проверен отдельно, production promotion/drift NOT_RUN; local mechanics доступны до R08 |
| R10 integration | [Архитектура](../projects/document_intelligence_lab/architecture.md) | Две независимые задачи, trust boundaries и таблица решений | [Пустая структура защиты](../projects/document_intelligence_lab/defense-template.md) | Teacher composition не равно полной системе; защита REQUIRES_REVIEW |
| R11 adaptation | [SFT masks и LoRA](../labs/04_llm_finetuning/theory.md) | Token/label table, low-rank shapes; measured train-loss SVG | Baseline/prompting/adapter comparison после разрешённых ресурсов | Actual CPU PEFT train/save/reload на tiny random LM проверен; pretrained/QLoRA NOT_RUN; ML-DEPTH |

R12 по уточнению пользователя — [только варианты специализации](superpowers/plans/2026-10-11-remaining-roadmap.md#r12).
Не добавляются отдельные CV/speech/ranking/platform курсы. Общие старые упражнения
переиспользуются как prerequisites, их TODO и критерии не подменяются teacher code.

Новый слой аудита: [качество объяснений ядра, пакет 1](#theory-packet-1), 04.10.2026.
Продолжение: [Pandas → качество → EDA → Matplotlib, пакет 2](#theory-packet-2).
Актуальное продолжение: [статистика и математический мост, пакет 3](#theory-packet-3).
Исторический статус COVERED ниже не означает достаточную глубину объяснения
каждого понятия; педагогическая проверка вынесена в пять отдельных столбцов.

Дата: 30.09.2026. Статус материалов: **READY; технические проверки — в журнале**.
Репозиторий: `C:\ProjectsDirectory\AIML\_road`, ветка `codex/ai-ml-wave1`,
HEAD `03a729bc3952df39793d8ccbdbbf64b08d6a123f`. Аудит включает незакоммиченные
материалы первой волны, а не только содержимое HEAD или удалённой main.

Источник требований — предоставленная пользователем проектная спецификация
`C:\Users\dimag\Downloads\Ml_roadmap_wave2_agent_prompt.md`.
Оригинальный дневник databossit не предоставлен и не изучался: ниже нет проверки
его результатов, метрик или трудоустройства. Предлагаемые задания — решения для
этого репозитория, не пересказ чужого учебного маршрута.

`COVERED` означает достаточный существующий материал/контракт, не выполненное
учеником задание. `NEEDS_DEPTH` — есть основа, но недостаёт указанной практики;
`MISSING` — проверяемой практики нет; `SPECIALIZATION` — сознательно вне ядра волны.
14 новых exercise ID зарегистрированы в CLI. Реестр содержит 162 материала:
57 lessons, 102 exercises, 2 labs, 1 project. TODO ученика сохранены, его
эксперименты NOT_RUN, содержательная защита REQUIRES_REVIEW. [Свежие проверки](wave2-verification.md)
не заменяют независимый итоговый review всей волны.

## Подготовленные продолжения и prerequisites

Все строки этой таблицы — материалы READY. Только три lab continuation требуют
training; старые lab targets не расширены. Ссылки ведут к editable boundaries,
командам и критериям каждого задания.

| ID / материал | Prerequisites | Свидетельство, которое готовит ученик |
| --- | --- | --- |
| [data-paired-model-comparison](../modules/03_data_foundations/exercises/paired_model_comparison/README.md) | data-statistics, data-paired-observations, ml-validation, ml-evaluation | Парный cluster bootstrap, CI/effect и ограничения |
| [data-randomized-experiment](../modules/03_data_foundations/exercises/randomized_experiment/README.md) | data-paired-model-comparison, data-statistical-profile | A/A–A/B, единицы назначения/анализа, guardrail и горизонт |
| [ml-knn-mechanics](../modules/04_machine_learning/exercises/knn_mechanics/README.md) | data-numpy, ml-preprocessing, ml-models, ml-training-bridge | Собственный kNN, формы/масштаб/сложность |
| [ml-tabular-study](../modules/04_machine_learning/exercises/tabular_study/README.md) | ml-model-comparison, ml-mixed-feature-pipeline, ml-threshold-policy, ml-evaluation-report, data-paired-model-comparison | Общие folds, ансамбли/один boosting, ablation, calibration, reload |
| [lab-training-resume](../labs/01_pytorch_foundations/exercises/resume_training/README.md) | lab-pytorch; training | Fresh-process resume, optimizer/RNG/sampler/cursor |
| [lab-training-diagnostics](../labs/01_pytorch_foundations/debugging/README.md) | lab-pytorch, ml-training-bridge; training | Контроль №3: четыре случая, гипотезы/следы/свои исправления |
| [lab-attention-mechanics](../labs/02_huggingface_models/attention_mechanics/README.md) | lab-huggingface, data-numpy; training | QKV, padding/causal masks, SDPA/gradient сравнение |
| [data-release-study](../modules/03_data_foundations/exercises/data_release/README.md) | python-io, python-paged-stream, python-testing, data-quality-report, data-library-joins | Контроль №1: выпуск данных, reject/provenance и память |
| [ml-evaluation-case](../modules/04_machine_learning/exercises/evaluation_case/README.md) | ml-tabular-study, ml-validation | Контроль №2: надёжность оценки, ограничения и свой протокол |
| [production-product-study](../modules/08_production_ai/exercises/product_study/README.md) | ml-problem-framing, ml-evaluation, production-serving, production-rollout | Контроль №4: ADR, бюджет, отказы, baseline и trade-offs |
| [rag-ranking-study](../modules/06_rag/exercises/ranking_study/README.md) | rag-vector-search, rag-rank-fusion, rag-retrieval-evaluation, rag-retrieval-regression | Corpus/judgments, semantic groups, два runs и парное сравнение |
| [ml-forecasting-intro](../modules/04_machine_learning/exercises/forecasting_intro/README.md) | data-time-split, ml-time-series-split, ml-models, ml-evaluation | One-step temporal backtest, naive/seasonal/Ridge и as-of признаки |
| [python-interview-patterns](../modules/01_python_core/exercises/interview_patterns/README.md) | python-collections, python-functions, python-typing, python-paged-stream | Вариации binary search/heap/BFS/DFS, сложность |
| [backend-analytics-sql](../modules/02_python_backend/exercises/analytics_sql/README.md) | backend-postgres-query, data-library-joins | SQLite результат, cardinality/window SQL и защита |

Открытые контроли ровно четыре; диагностика используется повторно как контроль №3.
Общий [шаблон защиты](project-defense.md) включает также incident-вариации.
Intro ranking/forecasting не означает готовность глубоких специализаций:
real RAG/tracking/PEFT/vLLM/lifecycle/Document Intelligence остаются PLANNED.

## Исходная карта аудита до реализации

Следующая таблица сохраняет исходные COVERED/NEEDS_DEPTH/MISSING и мотивировку
дополнений. Текущие подготовленные задания перечислены выше; её будущие формулировки
и отсутствие прежнего student ID относятся к началу волны.

| Компетенция | Реальные файлы / существующие ID | Текущее покрытие | Что требуется | Практическое свидетельство освоения |
| --- | --- | --- | --- | --- |
| Python, typing, коллекции, тестирование | [Module 01](../modules/01_python_core/README.md); `python-collections`, `python-functions`, `python-typing`, `python-testing`, `python-word-index` | COVERED: объяснения, примеры и отдельные student tests | Только prerequisites; не повторять курс Python | Собственные реализации проходят выбранный `check`, ученик объясняет новую вариацию |
| Shapes, vectorization, dot, нормы и геометрия | [NumPy](../modules/03_data_foundations/01_numpy/README.md), [retrieval geometry](../modules/06_rag/03_lexical_dense_retrieval/example.py); `data-numpy`, `data-image-pooling`, `rag-vector-search` | NEEDS_DEPTH: shapes/dot/vectorization есть; геометрия распределена, нет проверки связи расстояния и масштаба признаков | Короткие упражнения на формы матричного произведения/нормы внутри kNN, без нового курса линейной алгебры | Объяснение shape `n×d`, расстояния и изменения соседей при смене единиц |
| Производная, gradient, chain rule, descent | [Training bridge](../modules/04_machine_learning/07_training_bridge/README.md), [starter](../modules/04_machine_learning/07_training_bridge/starter.py); `ml-training-bridge` | COVERED для прикладного моста: скалярный пример и контракт векторного шага; полного собственного `.fit()` регрессора нет | Переиспользовать мост и regression; добавить проверку понимания частных производных/finite differences в диагностике, не второй regression-курс | Правильный gradient step и объяснение связи аналитической проверки с autograd |
| Байес, ожидание, дисперсия, описательные парные данные | [Practical statistics](../modules/03_data_foundations/04_practical_statistics/README.md), [paired observations](../modules/03_data_foundations/exercises/paired_observations/README.md); `data-statistical-profile`, `data-bayes-alert`, `data-paired-observations` | COVERED: контракты статистик и Bayes; covariance/correlation не являются сравнением качества моделей | Только ссылки из статистического углубления | Объяснение условной вероятности, единицы наблюдения и отсутствия причинного вывода из корреляции |
| CI, effect size, парное сравнение моделей | [Experiment protocol](experiment-protocol.md); прежнего student ID нет | MISSING: bootstrap упомянут, но нет реализации ученика и тестируемого контракта неопределённости | Парный cluster bootstrap для заранее выбранной разницы loss, сохранённые прогнозы и анализ сегментов | Пары не разорваны, группы пересэмплируются целиком; направление эффекта/CI/практическая значимость объяснены без обязательного победителя |
| A/A и A/B | [Experiment protocol](experiment-protocol.md); отдельного ID нет | MISSING: есть предупреждение, нет практики рандомизации/единицы анализа | Малый локальный опыт в том же статистическом блоке: единица назначения, целевая метрика, guardrail, заранее заданный горизонт | Повторные события одного объекта не превращаются в независимые наблюдения; нет обязательного p-value/улучшения; ограничения вывода защищены |
| Split, leakage, preprocessing, метрики | [Validation](../modules/04_machine_learning/02_validation/README.md), [mixed pipeline](../modules/04_machine_learning/03_preprocessing/exercises/mixed_feature_pipeline/README.md); `data-splits`, `ml-group-safe-split`, `ml-mixed-feature-pipeline`, `ml-evaluation-report` | COVERED: реальные упражнения и наблюдаемые fit/transform contracts | Переиспользовать в новых опытах, не переписывать | Split IDs, fit только внутри train folds, финальный test не выбирает конфигурацию |
| Linear/logistic, regularization, trees, kNN | [Models](../modules/04_machine_learning/04_models/README.md), [tree CV example](../modules/04_machine_learning/04_models/example.py), [model comparison](../modules/04_machine_learning/04_models/exercises/model_comparison/starter.py); `ml-models`, `ml-model-comparison` | NEEDS_DEPTH: Ridge/logistic/tree и CV есть, kNN-механики нет | Один новый маленький kNN `.fit/.predict`; регуляризация и чувствительность к масштабу — в объяснении/эксперименте | kNN совпадает с библиотекой на нетривиальных малых случаях; ученик объясняет стоимость fit/query и выбор k |
| Random Forest, bagging/boosting, feature engineering, bounded search | [Models](../modules/04_machine_learning/04_models/README.md), [предыдущий аудит §1](roadmap-coverage-review.md); `ml-model-comparison` | NEEDS_DEPTH: старое упражнение требует **ровно Dummy/Ridge/tree**; ансамбли только PLANNED | Отдельный нейтральный tabular experiment: Dummy → linear → tree/Forest → один sklearn HistGradientBoosting; feature ablation, ограничение поиска, reload | Общие folds, budget, EDA, реальная сохранённая pipeline и повторные predictions; сложная модель не обязана выиграть |
| Calibration, threshold, error analysis, interpretation | [Threshold policy](../modules/04_machine_learning/exercises/threshold_policy/starter.py), [evaluation report](../modules/04_machine_learning/06_reproducibility/exercises/evaluation_report/starter.py); `ml-threshold-policy`, `ml-evaluation-report`, `ml-evaluation` | NEEDS_DEPTH: threshold/Brier/slices уже тестируются; нет fit calibrator, reliability bins и feature interpretation | Встроить в тот же tabular classification experiment: sigmoid calibration на train folds, validation selection, permutation importance | Метрики пересчитаны из вероятностей; объяснены calibration vs ranking vs decision и некаузальность feature importance |
| PyTorch lifecycle | [Lab 01](../labs/01_pytorch_foundations/README.md), [tests](../labs/01_pytorch_foundations/test_starter.py); `lab-pytorch` | COVERED: loaders/module/forward/loss/backward/optimizer/validation/modes/checkpoint/inference | Ссылки/prerequisites; не создавать lab заново | Student tests проверяют режим во время forward, градиенты, optimizer state и reload, а не только финальный флаг |
| HF lifecycle и сравнение с classical baseline | [Lab 02](../labs/02_huggingface_models/README.md), [protocol](../labs/02_huggingface_models/protocol.py); `lab-huggingface` | COVERED: tokenization/preprocessing/batching/adaptation/eval/save/load/inference; offline random encoder и TF-IDF baseline; pretrained experiment NOT_RUN | Сохранить lab и явную отдельную загрузку; использовать её локальные fixtures | Реальные сохранённые weights/tokenizer, пересчёт inference; smoke не объявляется pretrained evaluation |
| Настоящий resume и диагностика обучения | [Lab 01 checkpoint tests](../labs/01_pytorch_foundations/test_starter.py), [предыдущий аудит §3](roadmap-coverage-review.md); `lab-pytorch`, `lab-huggingface` | NEEDS_DEPTH: restore optimizer и следующий шаг есть; непрерывная и возобновлённая траектории не сравниваются | Отдельные continuation IDs: mid-epoch resume и четыре нейтрально названных debugging case | В узком CPU-профиле совпадают sample order/steps и состояния с допуском; гипотезы → наблюдения → исправление → повторная проверка |
| Transformer internals | [HF theory](../labs/02_huggingface_models/README.md); `lab-huggingface` | NEEDS_DEPTH: tokenization/masks/encoder описаны; нет собственного attention-блока и полного shape trace | Q/K/V, padding/causal masks, residual/norm, encoder/decoder/encoder–decoder в существующей lab; отдельный маленький attention contract | Сравнение с PyTorch SDPA и gradients; влияние будущих/закрытых токенов отсутствует; invalid/all-masked поведение задано |
| Memory-aware data release | [Generators](../modules/01_python_core/07_iterators_generators/README.md), [paged stream](../modules/01_python_core/exercises/paged_stream/README.md), [quality](../modules/03_data_foundations/03_data_quality/README.md); `python-paged-stream`, `data-quality-report` | NEEDS_DEPTH: локальная ленивость есть, но нет целой bounded-memory цепочки с provenance/schema/labels; HF runner материализует малый CSV | Контроль «неудобные данные»: multifile local fixture, ambiguous labels, schema, duplicates, ограничение буферов; большой генератор только явно | Воспроизводимый data release, причины отклонений, rubric, manifest, измерения без хрупкого RSS-порога; неполный выпуск не принимается |
| Недостоверная оценка и открытая продуктовая задача | [Framing](../modules/04_machine_learning/01_problem_framing/README.md), [production](../modules/08_production_ai/README.md); `ml-problem-framing`, `production-release-gate`, `production-rollout-decision` | NEEDS_DEPTH: точные policy-контракты есть, двух открытых контролей нет | «Подозрительно хорошая модель» и «продуктовый выбор»: данные/цели/ограничения без выдачи причины или архитектуры | Собственная проверка оценки; ADR, бюджет, эксплуатация/отказы и доказательства; правила допустимы, защита REQUIRES_REVIEW |
| Ranking | [Retrieval evaluation](../modules/06_rag/06_rag_evaluation/exercises/retrieval_evaluation/starter.py), [paired regression](../modules/06_rag/exercises/retrieval_regression/starter.py), [RRF](../modules/06_rag/04_hybrid_reranking/README.md); `rag-retrieval-evaluation`, `rag-retrieval-regression`, `rag-rank-fusion`, `rag-vector-search` | NEEDS_DEPTH: метрики, парное сравнение запросов, fusion/ACL уже есть | Только сборка малого корпуса/judgments/semantic groups и двух retrieval runs; не новая реализация метрик | Одинаковые queries и доступ, query-level errors, incomplete judgments caveat; не метрики ответа LLM |
| Forecasting | [Temporal split](../modules/04_machine_learning/exercises/time_series_split/README.md); `ml-time-series-split`, `data-time-split`, `ml-validation` | NEEDS_DEPTH: временные folds есть; forecasting experiment нет | Короткий one-step forecast обращений: naive/seasonal baseline, lag/rolling/calendar и одна sklearn-модель | Явный as-of/horizon, признаки не видят цель; random-vs-temporal diagnostic без предписанного разрыва scores |
| Interview и защита | [Python](../modules/01_python_core/README.md), [PostgreSQL](../modules/02_python_backend/07_postgresql/README.md), [joins](../modules/03_data_foundations/exercises/library_joins/README.md); `python-paged-stream`, `backend-postgres-query`, `data-library-joins` | NEEDS_DEPTH: коллекции/потоки/SQL/joins есть; нет binary search/heap/BFS/DFS/window SQL и общей защиты | Два компактных набора вариаций + короткие incident cases и один шаблон защиты | Решение новой вариации, объяснение сложности/cardinality; результат SQL, а не совпадение текста запроса |
| Real RAG, tracking, PEFT, serving, lifecycle, Document Intelligence | [Next stages](ai-ml-extension-plan.md), [Document Intelligence](../projects/document_intelligence_lab/README.md) | SPECIALIZATION / PLANNED | Только сохранить prerequisites/артефакты/done; не реализовывать этой волной | Будущий отдельный отчёт о реальных экспериментах; сейчас NOT_RUN |

## Решения против дублирования

- Сохраняются все 148 существующих ID и student boundaries; число относится к
  состоянию **до** реализации wave 2. Подготовлены 14 дополнительных
  exercise ID, не 14 обязательных новых уроков.
- Собственный полный GD-регрессор сейчас отсутствует, но regression и gradient
  bridge уже есть. Выбрана **одна** новая ручная ML-модель — kNN; bridge/регрессию
  используем для самостоятельной проверки понимания, не дублируем.
- Calibration/threshold/interpretation входят в один tabular classification study,
  а не три новых проекта. Ранее предложенные в аудите отдельные tabular/calibration
  случаи объединяются здесь; прежний аудит остаётся исторической записью.
- Контроль «неудачное обучение» использует ровно те же debugging cases, не вторую
  диагностику. Четыре контроля размещаются в существующих modules/labs.
- Ranking переиспользует **и** evaluation, **и** готовый контракт парного сравнения
  `compare_retrieval`; это важнее, чем повторно написать recall под новым названием.
- Новые продолжения labs имеют отдельные test targets. Старые lab ID сохраняют
  прежний набор обязательных tests и не требуют wave 2 задним числом.
- CLI, зависимости и progress не требуют новой архитектуры. Ни SciPy, ни другой
  ML-framework не нужен для выбранного объёма.

## Порядок и критерий завершения

После имеющихся prerequisites: статистическое сравнение/A-A A-B → kNN и tabular
study → PyTorch/HF continuations. «Неудобные данные» доступно после Python I/O/
generators/testing + data quality. Продуктовый контроль — после опыта с данными,
оценкой и production constraints. Ranking идёт после Module 06 перед real RAG;
forecasting — короткая боковая ветка после ML validation. Interview-вариации
проходятся параллельно, не блокируют основные labs.

Для каждого нового большого блока: пример на другом случае → student contract →
диагностика → свой эксперимент → защита. Зелёный `test` означает здоровье материалов;
`check ID` проверяет обязательные код/артефакты только выбранного задания.
Качество вывода и защиты остаётся **REQUIRES_REVIEW** до человеческой проверки.

Подробные файлы, границы задач и тесты — в
[implementation plan](superpowers/plans/2026-09-30-ai-ml-wave2.md).
Свежие итоговые проверки и границы NOT_RUN — в
[wave2 verification](wave2-verification.md).

<a id="theory-packet-1"></a>

## Теория ядра: пакет 1 — 04.10.2026

Фактическая локальная база: `codex/ai-ml-wave1`, HEAD
`836028944eceaa260cb47d0056b593af4a4648d4`, включая незакоммиченный Object Model
pilot. Это состояние файлов, **не** отметки освоения. Существующий пилот и его
шаблон не переписаны; шаблон используется как ориентир объяснения, не как
обязательное требование рисовать каждую функцию.

### Что аудит счёл недостаточным

- Collections уже имел рабочий language summary и задачи на срезы/сортировку,
  но короткое перечисление не объясняло выбор контейнера, порядок, шаги
  comprehension и стоимость повторного `count`. Добавлено именно объяснение.
- Functions уже демонстрировал callback и имел практику, но не разбирал передачу
  функции против вызова, сбор/распаковку аргументов, время default и closure,
  ограничение `zip`. Новые реализации упражнений не нужны.
- Typing уже имел `LabelSource` и `SupportTicket`, но синтаксис и граница
  annotation/runtime оставались нераскрытыми. Добавлены narrowing, callable,
  alias/Literal и структурное сравнение с Java; пример сохранён.
- NumPy содержал рабочий SLA broadcast, notebook и две подходящие задачи, но
  не последовательное сопровождение всех восьми тем ниже. Старый пример и
  notebook сохранены; новый нейтральный walkthrough показывает взаимосвязи,
  не дублирует решение matrix/pooling.

### Пять свидетельств покрытия

«Есть» ниже означает конкретный подготовленный материал по ссылке. Прогнозы и
вариации не получают автоматически статус выполненных: **REQUIRES_REVIEW**.
Teacher-тесты подтверждают правильность объяснительных примеров, а не знания ученика.

| Тема / существующий ID | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Object Model / `python-object-model` | [Пилот](../modules/01_python_core/01_object_model/theory.md), сохранён | [example.py](../modules/01_python_core/01_object_model/example.py) | SVG имён/связей в пилоте | [Существующие задания](../modules/01_python_core/01_object_model/README.md#exercises) | Вопросы/вариации пилота + check выбранного ID; повторно не переработан |
| Collections / `python-collections` | [theory](../modules/01_python_core/02_collections/theory.md), §2–4 | Построчный language summary, срезы/ключ сортировки | Таблица выбора контейнера; отдельный рисунок не нужен | [slice windows](../modules/01_python_core/02_collections/exercises/slice_windows/README.md), `python-slice-windows` | Прогноз изменённого среза/ключа + check; объяснение порядка вручную |
| Functions / `python-functions` | [theory](../modules/01_python_core/03_functions/theory.md), §2–5 | Callback, collect/unpack, closure/default | Таблица этапов вызова | [configurable filter](../modules/01_python_core/03_functions/exercises/configurable_filter/README.md), `python-configurable-filter` | Предсказать ранний вызов/zip/default; check + устное объяснение |
| Typing / `python-typing` | [theory](../modules/01_python_core/04_typing/theory.md), notation/shape | Trace неизменённого normalize_labels | Таблица структурной совместимости и шагов | [Protocol](../modules/01_python_core/04_typing/exercises/payment_processor_protocol/README.md), `python-payment-processor-protocol` | Отличить mypy от runtime и несовместимую форму; check + ручная вариация |
| NumPy shape / `data-numpy` | [theory](../modules/03_data_foundations/01_numpy/theory.md), §1 | `(2, 3)`, ndim/size, сравнение `(3,)` | [Оси](../modules/03_data_foundations/01_numpy/assets/axes.svg) | [payment matrix](../modules/03_data_foundations/01_numpy/exercises/payment_matrix/README.md), `data-payment-matrix` | Прогноз формы новой таблицы вручную; shape contract в check |
| NumPy dtype | Та же theory, §2 | int32 + 0.5, itemsize | Таблица объёмов §7; отдельная схема не нужна | `data-payment-matrix` + новая вариация записи дроби в черновике | dtype контракт автоматический; объяснение promotion/потери дроби вручную |
| NumPy axis | Та же theory, §4 | sum по двум осям, keepdims | Схема осей с точными значениями | [image pooling](../modules/03_data_foundations/exercises/image_pooling/README.md), `data-image-pooling` | Прогноз mean/смысла оси; pooling check и объяснение четырёх осей |
| NumPy indexing | Та же theory, §3 | scalar/slice формы, пары индексов, mask | Таблица клеток на схеме осей + trace | Вариации индексов/маски в §3 (без нового ID) | Ручная сверка прогноза; отдельного автоматического зачёта indexing нет |
| NumPy broadcasting | Та же theory, §5 | Пороги каждого датчика, несовместимая форма | [Схема](../modules/03_data_foundations/01_numpy/assets/broadcasting.svg) | `data-payment-matrix` и вариация строки/столбцы | check + объяснение ошибки смысла при совместимой форме |
| NumPy view/copy | Та же theory, §6 | Две записи, shares_memory, reshape после transpose | [Схема состояний](../modules/03_data_foundations/01_numpy/assets/views.svg) | `data-image-pooling` + вариация explicit copy | check неизменности/независимости + прогноз после записи вручную |
| NumPy vectorization | Та же theory, §5 | Сравнение массива и Python-цикла | Схема broadcasting; новый рисунок не нужен | `data-payment-matrix`, затем `data-image-pooling` | В matrix AST исключает явные for/while/async for, но не comprehensions; способ векторизации обоих решений требует также ручной проверки; pytest не benchmark |
| NumPy memory | Та же theory, §7 | Малый broadcast_to и оценка без большой аллокации | Таблица payload/shared buffer | Изменить dtype/shape; бумажный бюджет 1 GiB | Ручная защита расчёта и временных результатов; это не измерение RSS и не student ID |

Ссылки `theory` ведут на самостоятельные документы с английскими терминами,
прогнозом → объяснением → шагами → ошибкой → вариацией. Проверяемые демонстрации:
[doctests](../tests/integration/test_theory_examples.py) и
[NumPy trace tests](../modules/03_data_foundations/tests/test_numpy_walkthrough.py).
Новые проверки инфраструктурные и не добавлены в test targets старых упражнений.
CLI, 162 ID, порядок обучения и progress сохраняются. Новых зависимостей нет.

### Следующие редакционные пакеты — PLANNED

Это порядок **доработки объяснений**, не новая последовательность обязательных
уроков. В этой итерации перечисленные файлы не реализуются заново.

1. **PLANNED — прикладной mathematical bridge и статистика.** После NumPy:
   [bridge](../modules/04_machine_learning/07_training_bridge/README.md),
   [statistics](../modules/03_data_foundations/04_practical_statistics/README.md).
   Проверить связку loss → gradient intuition → descent → autograd и интерпретацию
   оценки; переиспользовать текущие примеры/контракты. Результат: трассируемое
   объяснение и новая устная вариация без готового student gradient.
2. **PLANNED — табличные данные и классическое ML.** После NumPy/существующих
   data-quality/split: [Pandas](../modules/03_data_foundations/02_pandas_core/README.md),
   [ML](../modules/04_machine_learning/README.md). Аудировать объяснения alignment,
   leakage/preprocessing/metrics и причин выбора baseline; не повторять задачи.
   Результат: связь данных, оценки и выбора модели, подтверждённая шагами примера.
3. **PLANNED — диагностика обучения и Transformers.** После bridge и ML:
   [PyTorch](../labs/01_pytorch_foundations/README.md),
   [Hugging Face](../labs/02_huggingface_models/README.md). Аудировать объяснения
   lifecycle/resume и attention shape trace, переиспользуя уже созданные continuations.
   Результат: предсказание состояния/ошибки на малом примере; не новый training stack.
4. **PLANNED — остальное ядро по результатам аудита.** После оценки предыдущих
   пакетов: Python I/O/generators, backend, LLM/RAG/agents/production. Дополнения
   только при доказанном пробеле; не рисовать каждый метод и не объявлять
   специальности из [next stages](ai-ml-extension-plan.md) реализованными.

Фактические проверки пакета, ограничения и список файлов:
[theory packet 1 verification](theory-packet-1-verification.md).

<a id="theory-packet-2"></a>

## Теория ядра: пакет 2 — 04.10.2026

База та же: `codex/ai-ml-wave1`, HEAD `836028944eceaa260cb47d0056b593af4a4648d4`,
с сохранённым незакоммиченным пакетом 1. Расширены существующие `data-pandas`
и `data-quality`; новый курс, notebook и новые ID не создавались.
Здесь «подготовлено» относится к материалу, **не** к освоению учеником.

### Фактический пробел и принятое ограничение

До пакета короткий Pandas README перечислял операции и запускал корректную
группировку четырёх support tickets, но не объяснял выравнивание по меткам,
размножение строк merge и политику пропусков/типов. Data quality уже имел
пример четырёх документов и проверяемые упражнения, но не причинный разбор
дефектов и решений. Notebook по Pandas и нейтральные weather/library упражнения
сохранены; они не заменяют объяснение EDA и построения графиков.

Добавлены сопровождающие тексты, четыре графика с числовыми основаниями и
ручное EDA-продолжение **существующего** `data-weather-quality`. Демонстрация
на support tickets полностью разобрана, погодное решение отсутствует.
Matplotlib отсутствовал в зависимостях: теперь только opt-in группа
`visualization`; базовый `uv sync` не устанавливает её. Seaborn/Plotly не добавлены.

### Пять свидетельств покрытия пакета 2

| Тема / действующий ID | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Series/DataFrame/Index / `data-pandas` | [theory](../modules/03_data_foundations/02_pandas_core/theory.md), §1–2 | Две комнаты, противоположный порядок bonus | Таблица соответствий меток и сумм | Вариация новой метки §2; без нового ID | Предсказать индекс/NA/значение; pycon проверяет только автора |
| loc/iloc, фильтр, сортировка | Та же theory, §3–4 | Срез по меткам против позиции, маска и два ключа | Массивы меток до/после, отдельный рисунок не нужен | Вариации перестановки и порога | Объяснить включение границы/сохранение индекса вручную |
| NA, duplicates, dtype | Та же theory, §5 | Поэтапная выборка и to_numeric | Маски и одна итоговая запись | [data-transaction-summary](../modules/03_data_foundations/02_pandas_core/exercises/transaction_summary/README.md) | Старый check контракта + объяснить порядок правил |
| groupby/aggregation | Та же theory, §6–7 | Сохранённый support-ticket example; size/count/observed | Входная таблица → группы → точный результат | `data-transaction-summary`, вариация пропущенного ID | Предсказать count и mean отдельно; check + ручной перенос |
| merge/join, cardinality | Та же theory, §8 | Комнаты: 3 → 3 и 3 → 5 | Малые входные/выходные таблицы | [data-library-joins](../modules/03_data_foundations/exercises/library_joins/README.md), [data-merchant-join](../modules/03_data_foundations/02_pandas_core/exercises/merchant_join/README.md) | Прогноз строк, many-to-one и null-ключей; существующие check |
| Даты и timezone | Та же theory, §9 | Смещение времени меняет UTC-день | Два момента до/после разбора | Вариация timezone; затем погодные даты | Предсказать день до запуска, не путать разбор с контрактом |
| Pandas 3 mutation | Та же theory, §10 | Изменение выбранной Series и явная loc-запись | Два результата до/после | Вариация и обещание неизменности аргумента | Отличить CoW от NumPy view и Python alias вручную |
| Качество и provenance / `data-quality` | [theory](../modules/03_data_foundations/03_data_quality/theory.md), §1–7 | Неизменённый document example + маски разных дефектов | Таблица четырёх документов, маски, trace счёта | [data-weather-quality](../modules/03_data_foundations/exercises/weather_quality/README.md); существующий quality report | Старый check + семь вопросов о ключах, счётах, решениях |
| EDA: вопрос → качество → наблюдение | [eda](../modules/03_data_foundations/03_data_quality/eda.md), §1–3 | 12 support-ticket строк → 11 записей → разные n | Таблицы схемы/решений/оснований | [Погодный практикум](../modules/03_data_foundations/exercises/weather_quality/eda_practice.md) | Реестр причин и выборок, объяснение ограничений; REQUIRES_REVIEW |
| Matplotlib Figure/Axes | Та же eda, §4, 9 | [eda_demo.py](../modules/03_data_foundations/03_data_quality/eda_demo.py) сохраняет четыре PNG | Схема объектов + реальные PNG | Свои четыре погодных графика | Читаемые единицы/легенды/сохранение, ручная проверка |
| Распределение/связь/группы/время | Та же eda, §5–8 | Частоты bins, пары одной строки, mean/n, даты с NA | Четыре картинки из того же кода и точные таблицы | Тот же связный практикум, без готовых выводов | Для каждого: вопрос, наблюдение, чего не доказывает; REQUIRES_REVIEW |

### Место в маршруте и границы проверки

После NumPy: Pandas theory и старый пример → существующие summary/joins по
необходимости → quality theory и старый пример → EDA на support tickets →
самостоятельная погода → практическая статистика и прежний порядок модуля.
ML-понятия из будущих уроков не являются prerequisites для новых пояснений.

[Teacher transcripts](../modules/03_data_foundations/tests/test_packet2_theory.py)
проверяют числовые результаты в текстах, [EDA tests](../modules/03_data_foundations/tests/test_eda_demo.py)
— аудит, выборки, координаты графиков, экспорт и защиту от перезаписи.
Эти tests расположены вне старых student targets. Без группы visualization
пропускаются лишь три новых проверки отрисовки; расчёты проверяются и в базе.
`check data-weather-quality` **не оценивает** новый самостоятельный анализ.
Смысл `test/check`, 162 ID, старые контракты и progress не изменены.

### Следующие редакционные пакеты — PLANNED

Этот актуальный порядок уточняет исторический список пакета 1 выше; он не
меняет порядок обязательных уроков и не означает начало новой реализации.

1. **PLANNED — прикладная статистика и mathematical bridge.** После NumPy и
   опыта EDA: [statistics](../modules/03_data_foundations/04_practical_statistics/README.md)
   и [bridge](../modules/04_machine_learning/07_training_bridge/README.md).
   Разобрать основания оценки и loss/градиент шаг за шагом на текущих примерах.
2. **PLANNED — классическое ML.** После статистики и split: существующие
   [ML-уроки](../modules/04_machine_learning/README.md). Объяснить preprocessing,
   baseline/metrics и диагностику без повторения уже разобранного Pandas.
3. **PLANNED — диагностика обучения и Transformers.** После ML/bridge:
   [PyTorch](../labs/01_pytorch_foundations/README.md) и
   [Hugging Face](../labs/02_huggingface_models/README.md), lifecycle/resume/attention.
4. **PLANNED — остальное ядро после оценки пакетов.** Аудит I/O, backend,
   LLM/RAG/agents/production; большие специализации остаются в
   [next stages](ai-ml-extension-plan.md), без реализации этой итерацией.

Что создано, какие проверки реально выполнены и что остаётся ученику:
[журнал пакета 2](theory-packet-2-verification.md).

<a id="theory-packet-3"></a>

## Теоретический пакет 3: статистика и математический мост

Дата: 04.10.2026. Этот раздел дополняет, а не заменяет исторические записи выше.
Материалы подготовлены; технические результаты и ограничения — в
[журнале пакета 3](theory-packet-3-verification.md). Понимание ученика НЕ ПРОВЕРЕНО.

Исходный аудит: в `data-statistics` были короткий README, медиана в `example.py`
и контракты профиля/Bayes/пар. Не хватало объяснения знаменателей, единиц и
изменчивости оценки. В `ml-training-bridge` уже были скалярные
`loss/gradient/step`, векторный TODO и вопросы на производные; не хватало полного
ручного прохода, форм и сравнения размеров шага. Эти функции и задания
переиспользованы, не заменены новыми реализациями.

### Покрытие: объяснение → пример → опора → перенос → проверка

| Тема | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Наблюдение, выборка, совокупность, распределение | [Статистика §1](../modules/03_data_foundations/04_practical_statistics/theory.md#1-что-считается-наблюдением) | Пять заявок, единица строки | Малый массив; таблица двух выборок в §8 | Клиенты против заявок | Ручное объяснение отбора и зависимых строк |
| Среднее, медиана, квантили, асимметрия | [§2–3](../modules/03_data_foundations/04_practical_statistics/theory.md#2-почему-одно-необычное-значение-меняет-историю) | Замена 17→300; позиция процентиля 3.8 | `assets/outlier.png` | Замена 300→30; `data-statistical-profile` | Ручной расчёт; check проверяет реализацию, не выбор статистики |
| Дисперсия и стандартное отклонение | [§4](../modules/03_data_foundations/04_practical_statistics/theory.md#4-насколько-разбросаны-сами-времена) | Сумма квадратов 50, деление на 5 или 4 | Формулы с единицами; график статистик в минутах | Сдвиг всех наблюдений на 2 | Прогноз, расчёт; обоснование ddof вручную |
| Вероятность, условие, независимость, Байес | [§5–6](../modules/03_data_foundations/04_practical_statistics/theory.md#5-почему-условная-вероятность-меняет-знаменатель) | 30/40 против 30/42, две ветви знаменателя | Таблица частот с итогами | Изменить ячейку; `data-bayes-alert` | Расчёт и объяснение условия после черты |
| Ковариация и корреляция | [§7](../modules/03_data_foundations/04_practical_statistics/theory.md#7-вместе-ли-меняются-два-числовых-признака) | Три пары: cov=0.5, r=0.5 | Векторы отклонений и произведений | Новая последняя y; `data-paired-observations` | Ручные единицы/контрпример; старые tests проверяют пары |
| Разброс наблюдений и изменчивость оценки | [§8](../modules/03_data_foundations/04_practical_statistics/theory.md#8-проверка-перенос-и-источники) | Два ручных повтора; 500 IID выборок n=5/50 | `assets/sampling.png`, одинаковые шкалы | Новый seed, сверка CSV, ошибочное объяснение | Числа/воспроизводимость — tests; обоснование IID — вручную |
| Прогноз → остаток → loss → производная → шаг | [Мост §1–4](../modules/04_machine_learning/07_training_bridge/theory.md) | 0.7→1.02; loss 2.56→0.9216; chain rule | Цепочка, таблица производных, `assets/descent.png` | Другой старт/цель на бумаге; `ml-training-bridge` | Направление/единицы вручную; tests проверяют трассу, не качество модели |
| Learning rate, частные производные, формы, autograd | [Мост §4–6](../modules/04_machine_learning/07_training_bridge/theory.md#4-размер-шага-и-численная-проверка) | Цикл при 0.25, рост при 0.3; две координаты | Loss по шагам; формы `(n,d)`, `(d,)`, `(n,)` | Свой `gradient_step`; объяснение broadcasting и finite difference | Прежний check не расширен; перенос понимания требует ручного review |

### Маршрут и границы зачёта

Часть A — существующая [Practical statistics](../modules/03_data_foundations/04_practical_statistics/README.md)
в Data Foundations после NumPy/Pandas/качества/EDA. Мост не является её prerequisite.
Часть B — существующий [Training bridge](../modules/04_machine_learning/07_training_bridge/README.md)
после NumPy, ML framing, validation, models/regression и evaluation, перед PyTorch.
Материалы пакета не переставляют эти уроки.

Новых ID нет: вычислительные умения уже имеют задания, а новые объяснения
проверяются ручной самопроверкой. [Статистические demo tests](../modules/03_data_foundations/tests/test_statistics_demo.py),
[скалярные demo tests](../modules/04_machine_learning/tests/test_descent_demo.py) и
[транскрипты](../tests/integration/test_packet3_theory.py) — авторские инфраструктурные
проверки, вне старых student targets. Они не засчитывают ученику новое продолжение.

Зависимые данные/cluster bootstrap продолжаются в
[`data-paired-model-comparison`](../modules/03_data_foundations/exercises/paired_model_comparison/README.md)
после статистики, пар, ML validation и evaluation. Затем
[`data-randomized-experiment`](../modules/03_data_foundations/exercises/randomized_experiment/README.md)
добавляет единицу рандомизации/A/A–A/B; также нужен statistical profile.
Эти задания не дублируются, их TODO не решены.

Новых зависимостей нет. Числа работают в базе; PNG — в имеющейся opt-in группе
`visualization`. Данные синтетические локальные. Экспорт — явной командой
в новую папку с параметрами, версиями и исходными числами; браузер не открывается.

### Следующие редакционные пакеты — PLANNED

1. **PLANNED — классическое ML и оценка.** Следующий пакет объяснений существующих
   [ML-уроков](../modules/04_machine_learning/README.md) после статистики и split,
   без повторения Pandas/NumPy и без переноса bridge в начало ML.
2. **PLANNED — диагностика обучения и Transformers.** Углубление существующих
   [PyTorch](../labs/01_pytorch_foundations/README.md) и
   [Hugging Face](../labs/02_huggingface_models/README.md) после ML/bridge.
3. **PLANNED — остальное ядро после оценки пакетов.** Ранее обозначенные
   [следующие этапы](ai-ml-extension-plan.md) остаются планами, не реализацией.

<a id="theory-packet-4"></a>

## Теоретический пакет 4: классическое ML, выбор и оценка

Дата: 04.10.2026. Это актуальное дополнение к истории выше: отметка пакета 4
как PLANNED в предыдущем разделе описывает состояние **до** этой итерации.
Созданы объяснения; освоение учеником **НЕ ПРОВЕРЕНО**. Технические результаты
и ограничения собраны в [одном отчёте](theory-packet-4-verification.md).

### Аудит и решение против дублирования

До пакета шесть уроков Module 04 имели короткие преимущественно английские
README и работающие отдельные examples. Упражнения уже задавали честные folds,
смешанный pipeline, сравнение моделей, thresholds, полный tabular study и
контроль качества оценки. Значит, пробел — связное объяснение механизмов
и переход между этими умениями, а не нехватка новых упражнений.

Добавлены `theory.md` рядом с существующими README, два преподавательских
сценария в [classical_demo.py](../modules/04_machine_learning/06_reproducibility/classical_demo.py)
и авторские проверки. Исходные examples, ensemble-разборы, contracts и fixtures
переиспользованы ссылками, не заменены. Нет нового exercise ID, второго
табличного проекта, готового kNN или решения `ml-evaluation-case`.

### Пять свидетельств покрытия

| Тема | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Unit, X/y, as-of, цель и польза | [Framing](../modules/04_machine_learning/01_problem_framing/theory.md) | Контракт новой машины, признаки до осмотра; baseline | Таблица контракта и доступности | Прежний `ml-problem-framing`: свой контракт; затем `ml-model-comparison` | Вручную защитить единицу, горизонт, правило без ML; tests не оценивают текст |
| Split, CV, параметры/гиперпараметры, leakage | [Validation](../modules/04_machine_learning/02_validation/theory.md) | Группы S1–S4, weather windows; fold means 16/11.5/6.5 | Таблица ролей и схема каждого fit | [`ml-group-safe-split`](../modules/04_machine_learning/02_validation/exercises/group_safe_split/README.md), `ml-time-series-split` | Прогноз новых строк/групп; обоснование deployment вручную; старые checks проверяют split |
| Fit/transform, schema, feature engineering | [Preprocessing](../modules/04_machine_learning/03_preprocessing/theory.md) | Train 1/3 → mean 2, новая 100 → 98; numeric/category ветви | Вход → состояние → transform; Pipeline/ColumnTransformer | [`ml-mixed-feature-pipeline`](../modules/04_machine_learning/03_preprocessing/exercises/mixed_feature_pipeline/README.md) | Вариация с экстремумом/новой категорией, отсутствие изменения fitted state |
| Linear/logistic, regularization | [Models](../modules/04_machine_learning/04_models/theory.md) | Вклады 8+3×6+4×2=34; sigmoid(2)≈0.881 | Формула с единицами и подстановка; score → probability → decision | [`ml-model-comparison`](../modules/04_machine_learning/04_models/exercises/model_comparison/README.md) | Объяснить scale/alpha/C, предсказать новую строку; сравнение на одинаковых folds |
| kNN и дерево | [Models](../modules/04_machine_learning/04_models/theory.md) | Смена ближайшего соседа после масштаба; ветвь → лист | Таблица расстояний и путей; measured depth/error plot | Тот же model comparison; [`ml-knn-mechanics`](../modules/04_machine_learning/exercises/knn_mechanics/README.md) **после прежних prerequisites, включая bridge** | Ручной прогноз и собственная вариация, затем прежние tests; алгоритм за ученика не дан |
| Bagging, RF, boosting | [Models](../modules/04_machine_learning/04_models/theory.md) | Усреднение прогнозов; остатки для squared loss; прежний sensor ensemble example | Числовая последовательность; шесть вопросов разобраны в тексте, отдельного рисунка нет | [`ml-tabular-study`](../modules/04_machine_learning/exercises/tabular_study/README.md) | Защита различий ансамблей; tests не требуют победы сложной модели |
| MAE/MSE/RMSE, outliers, единицы | [Evaluation §1](../modules/04_machine_learning/05_evaluation/theory.md) | Прежние 4 поездки: MAE 3.5, MSE 26.5, RMSE≈5.1478 | Таблица/вектор ошибок, test residual histogram | `ml-model-comparison`, `ml-evaluation-report` | Изменить один большой промах; пересчитать и объяснить различие |
| Confusion, labels/scores/probas, ROC/AP/PR | [Evaluation §2–3](../modules/04_machine_learning/05_evaluation/theory.md) | Четыре объекта: AUC .75, AP .8333, trapezoid .7917 | Таблица исходов и матрица | [`ml-threshold-policy`](../modules/04_machine_learning/exercises/threshold_policy/README.md), `ml-multiclass-report` | Ручные подсчёты; отличить ранжирование от решений и вероятностей |
| Calibration, cost, threshold | [Evaluation §3–4](../modules/04_machine_learning/05_evaluation/theory.md) | Reliability bin (.70,.40), n=10; отдельные 24 calibration/24 selection | Cost по трём порогам, frozen test confusion | `ml-threshold-policy`, `ml-tabular-study` | Не обучать calibrator/выбирать threshold на test; цену/метрику задать до сравнения |
| Срезы, uncertainty, interpretation | [Evaluation §5](../modules/04_machine_learning/05_evaluation/theory.md) | Ошибки с support; sklearn permutation на validation | Числа `error_slices` в отчёте и разбор в reproducibility; отдельного рисунка нет | `ml-tabular-study`, [`data-paired-model-comparison`](../modules/03_data_foundations/exercises/paired_model_comparison/README.md), [`ml-evaluation-case`](../modules/04_machine_learning/exercises/evaluation_case/README.md) | Ручная защита noncausal/малого n; статистика переиспользована, контроль не раскрыт |
| Полный lifecycle и воспроизведение | [Reproducibility](../modules/04_machine_learning/06_reproducibility/theory.md) | Cycling и sensors: split → fit → selection → frozen test → save/reload | Роли данных, таблица артефактов, два измеренных PNG | [`ml-evaluation-report`](../modules/04_machine_learning/06_reproducibility/exercises/evaluation_report/README.md), `ml-tabular-study` | Пересчёт по predictions; собственное исследование и ручная защита отдельно |

### Маршрут и границы

[Module 04 README](../modules/04_machine_learning/README.md) → уроки 01–06 в
прежнем порядке → [математический мост](../modules/04_machine_learning/07_training_bridge/README.md)
→ [PyTorch](../labs/01_pytorch_foundations/README.md). NumPy, Pandas, статистика
и мост не переписаны. Два новых сценария используют локальные синтетические
преподавательские данные; production-качество не заявляется.

[Lifecycle tests](../modules/04_machine_learning/tests/test_classical_demo.py)
проверяют границы fit/selection/test, сохранённые байты, schema, replay и графики;
[transcript tests](../tests/integration/test_packet4_theory.py) выполняют расчёты
из теории. Это авторская проверка, не новый объём старых `check`.
Student TODO/reports, `progress.md`, curriculum ID/prerequisites и CLI сохранены.
Новых зависимостей нет: числовой маршрут базовый, графики opt-in `visualization`.

Следующий пакет **PLANNED — обучение моделей и Transformers**: после ML/bridge
углубить существующие PyTorch/Hugging Face, диагностику/resume/attention.
Он не реализован этим пакетом; остальные [следующие этапы](ai-ml-extension-plan.md)
остаются PLANNED.

<a id="theory-packet-5"></a>

## Теоретический пакет 5 — обучение нейросетей и Transformers

Дата: 04.10.2026. Это дополнение к истории, не замена предыдущих пакетов.
Отметка пакета 5 как PLANNED выше относится к прежнему состоянию.
Подготовлена теория существующих лабораторных; понимание ученика **НЕ ПРОВЕРЕНО**.
Результаты команд и ограничения — в [едином отчёте](theory-packet-5-verification.md).

### Что показал аудит и что переиспользовано

Математический мост уже подробно разбирал скалярный loss, chain rule, конечные
разности и шаг градиентного спуска. Lab 01 задавала полный lifecycle, формы,
контракты batch/validation/checkpoint. Resume уже имел RNG/cursor/momentum,
diagnostics — отдельные расследования. Здесь недоставало численного прохода
через нелинейную сеть и объяснения перехода от наблюдения сбоя к проверке гипотез.
Мост, starter, fixtures и проверки этих заданий не переписаны.

Lab 02 и attention mechanics уже задавали токенизацию, pooling, формулы и маски.
Пробелом были фактический путь tokenizer → encoder → head, ручная арифметика
одной головы и сопоставление противоположных соглашений о boolean mask.
Переиспользованы `make_local_components`, старый save/load smoke и прежний
ученический attention-контракт; случайный encoder не назван pretrained.

### Пять свидетельств покрытия

| Тема | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Признаки, параметры, affine-слой, ReLU | [PyTorch theory §1–2](../labs/01_pytorch_foundations/theory.md) | Один пиксель → 16→8→2 → logits `[1,0]` | Таблица форм, граф с числами | Прежний `lab-pytorch`; вариация цели на бумаге | Предсказать формы и влияние координаты; защита вручную |
| Logits, loss, metric, regression/classification | [§2](../labs/01_pytorch_foundations/theory.md#2-один-проход-по-сети-с-единым-соглашением-о-формах) | CE≈0.313261688; правильный класс при ненулевом loss | Подстановка softmax/log и таблица осей | Тот же `lab-pytorch`, без расширения check | Объяснить dtype/форму цели и почему не softmax перед CE |
| Граф, gradients, SGD, accumulation | [§3](../labs/01_pytorch_foundations/theory.md#3-обратный-проход-и-реальное-изменение-параметров) | Шесть производных и обновлений; конечная разность одной координаты | Граф зависимостей и таблица до/grad/после | Бумажная смена target/lr; затем свой цикл | [Авторские tests](../labs/test_packet5_pytorch.py) сверяют числа; объяснение chain rule вручную |
| Batches, modes, validation, reload | [§4](../labs/01_pytorch_foundations/theory.md#4-что-происходит-за-эпоху) | Прежние ShapeImages/ShapeNet: батчи 6/6/6/1, четыре эпохи | Вывод [walkthrough](../labs/01_pytorch_foundations/walkthrough.py), опциональный `learning.png` | `lab-pytorch`, далее [`lab-training-resume`](../labs/01_pytorch_foundations/exercises/resume_training/README.md) | Count, row-weighted loss, отсутствие изменения весов validation, reload; защита inference/resume |
| Диагностика, регуляризация, состояние optimizer | [§5–6](../labs/01_pytorch_foundations/theory.md#5-если-обучение-выглядит-неправильным) | Симптом → конкурирующие причины → различающее измерение | Таблица расследования, без ответов A–D | [`lab-training-diagnostics`](../labs/01_pytorch_foundations/debugging/README.md) | Собственное измерение/обоснование; не автоматическая оценка текста |
| Tokens/IDs, padding/truncation, embeddings | [HF theory §1–2](../labs/02_huggingface_models/theory.md) | `red` и `large blue square`: настоящие ID локального tokenizer | Таблица текст→ID→формы | `lab-huggingface`: свой `encode_batch`, бумажная вариация длины | [Авторские tests](../labs/test_packet5_huggingface.py) фиксируют фактический вывод; прогноз ученика вручную |
| Encoder, pooler, head, frozen vs adapted | [§2 и §5](../labs/02_huggingface_models/theory.md#5-три-режима-и-полный-эксперимент) | BERT `[2,5,16]`→CLS pooler `[2,16]`→logits `[2,2]`; отличается от MiniLM mean+L2 | Таблица форм; три режима в тексте | Старый `lab-huggingface`, baseline TF-IDF на тех же splits | Различить замороженные параметры и отключённый граф; реальный pretrained experiment NOT_RUN |
| Q/K/V, scaling, row softmax, masks | [§3](../labs/02_huggingface_models/theory.md#3-одна-голова-attention-от-поиска-к-сумме) | `[1,0,-∞]` → `[.731059,.268941,0]` → `[1.462117,1.075766]` | Ручная строка; опциональная `attention.png`; таблица API масок | [`lab-attention-mechanics`](../labs/02_huggingface_models/attention_mechanics/README.md) | Изменить разрешённый/закрытый value, рассчитать другую query; старые output/gradient tests сохранены |
| Multi-head, residual/norm/FFN, семейства | [§3–4](../labs/02_huggingface_models/theory.md#4-attention-внутри-transformer-и-типы-моделей) | BERT: 2 головы × 8; FFN 16→24→16; концептуальный next-token шаг | Формы и таблица encoder/decoder/encoder–decoder | Вопросы к прежним HF/attention заданиям, без нового ID | Объяснить доступный контекст и различие `[B,C]`/`[B,T,Vocab]` вручную |

### Последовательность и границы

Прежний маршрут: ML → [математический мост](../modules/04_machine_learning/07_training_bridge/README.md)
→ [PyTorch README](../labs/01_pytorch_foundations/README.md) и его новая теория
→ собственный `lab-pytorch` → продолжения resume/diagnostics по их prerequisites
→ [Hugging Face README](../labs/02_huggingface_models/README.md) и новая теория
→ прежние HF/attention задания. Базовое объяснение доступно **до** их TODO.
Часть А технически проверена до реализации Б.

Две семьи преподавательских демонстраций используют отдельные синтетические
данные/новые выходные каталоги и прежние fixtures; они не создают submissions.
Новые author tests лежат вне старых student targets. `test` допускает xfail;
`check ID` по-прежнему проверяет конкретную ученическую работу. IDs, prerequisites,
CLI, progress, старые examples и TODO сохранены. Зависимости/lock не изменены
этим пакетом; используются существующие `training` и `visualization`.

**PLANNED:** следующее углубление LLM Engineering/RAG и все ещё не реализованные
[реальные лабораторные](ai-ml-extension-plan.md), включая real embeddings/vector DB/RAG,
tracking, PEFT/LoRA/QLoRA, serving/vLLM, drift/lifecycle и Document Intelligence.
Механический smoke не переводит их в READY и не удостоверяет качество модели.

<a id="theory-packet-6"></a>

## Теоретический пакет 6 — LLM Engineering и RAG

Дата: 04.10.2026. Это дополнение к истории выше, не замена прежних пакетов.
Аудит обнаружил корректные, но короткие объяснения и раздельные examples.
Нужны были связи между ними и разбор решений приложения, а не новые exercise ID.
Старые interfaces, examples, student contracts, prerequisites и `test/check` сохранены.
Технические результаты и ограничения — в [едином отчёте](theory-packet-6-verification.md).
Понимание ученика **НЕ ПРОВЕРЕНО**.

Часть А подготовлена и технически проверена до начала реализации Б.
Часть Б продолжает тот же синтетический сервисный справочник реальным локальным
TF-IDF поиском. Ответы явно подготовлены автором, а не сгенерированы моделью.

### Пять свидетельств покрытия LLM Engineering

| Тема | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Модель, runtime, API и генерация | [LLM 01](../modules/05_llm_engineering/01_llm_interfaces/theory.md) | Задача велосервиса; условные вероятности 0.6/0.3/0.1, top-p | Цепочка запроса и ручная нормировка | Прогноз при `length`; старый `llm-interfaces`, затем `llm-bounded-retry` | Объяснить ответственность adapter и пределы decoding; не выдать fixture за модель |
| Prompt/context, роли и доступ | [LLM 02](../modules/05_llm_engineering/02_prompt_contracts/theory.md) | Открытый G-01 и отказ передачи staff guide | Таблица частей запроса | [`llm-prompt-messages`](../modules/05_llm_engineering/02_prompt_contracts/exercises/prompt_messages/README.md), ручная injected instruction | Показать точку ACL до контекста; роли/кавычки не доказательство защиты |
| Schema, смысл, evidence и действие | [LLM 03](../modules/05_llm_engineering/03_structured_outputs/theory.md) | Корректная цитата, не подтверждающая `available` | Таблица пяти проверок и исходов | [`llm-event-contract`](../modules/05_llm_engineering/03_structured_outputs/exercises/event_contract/README.md) | Предсказать первый отказ; разобрать границу узкого known-fact gate |
| Полный бюджет, резерв и стоимость | [LLM 04](../modules/05_llm_engineering/04_context_and_cost/theory.md) | Условные 80+20=100; старый Decimal example 0.0048 | Состав бюджета по частям | `llm-context-budget`, `llm-context-packing` по ссылкам урока | Пересчитать изменение; отличить слова/символы от model tokens |
| Качество, latency/cost, held-out | [LLM 05](../modules/05_llm_engineering/05_evaluation/theory.md) | Unsupported ответ при существующей citation; старый release example | Диагностическая таблица | [`llm-answer-evaluation`](../modules/05_llm_engineering/05_evaluation/exercises/answer_evaluation/README.md), защита рубрики | Разделить unit test, эталон/поддержку, реальное измерение и judge |
| Timeout/retry/stream, tools и cache | [LLM 06](../modules/05_llm_engineering/06_reliability_and_tools/theory.md) | Отказ, обрезанный JSON, запрет передачи контекста; прежний lookup | Успешная/неуспешная [teacher trace](../modules/05_llm_engineering/walkthrough.py) | `llm-bounded-retry`, `llm-stream-assembly`, `llm-response-cache` | Обосновать повтор, deadline, полномочия и безопасный журнал; TODO остаются самостоятельными |

### Пять свидетельств покрытия RAG

| Тема | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Полный pipeline, контракт и происхождение | [RAG 01](../modules/06_rag/01_retrieval_contracts/theory.md) | G-01: исходник → разрешённый chunk → ответ | Таблица вход/выход/сбой/проверка каждого этапа | Предсказать этап потери evidence; прежний `rag-contracts` | Объяснить каждый переход и отличие prepared answer от генерации |
| Нормализация, chunking, версии и удаления | [RAG 02](../modules/06_rag/02_ingestion_chunking/theory.md) | Два абзаца G-01 и устаревшая ревизия | До/после chunking; IDs, revision, digest | `rag-text-chunking`, `rag-index-sync` по ссылкам урока; объяснить потерю условия | Старые проверки плюс ручная защита выбора границы; student TODO не решены |
| Lexical/dense, геометрия и пределы поиска | [RAG 03](../modules/06_rag/03_lexical_dense_retrieval/theory.md) | TF-IDF 0.525060; лексический промах `night shelter` | Реальные ранги/scores; сравнение retrieval и index | [`rag-vector-search`](../modules/06_rag/03_lexical_dense_retrieval/exercises/vector_search/README.md); прогноз top-k | Отличить OOV от отсутствия факта, similarity от truth; механика проверена author tests |
| Fusion, reranking, разнообразие | [RAG 04](../modules/06_rag/04_hybrid_reranking/theory.md) | Ручной RRF 1/61+1/62; равенство результатов | Два ранжированных списка и арифметика | `rag-rank-fusion`, `rag-context-diversity` по ссылкам урока | Объяснить потерянного кандидата и почему сложность не гарантирует улучшение |
| Контекст, цитаты, доступ и конфликты | [RAG 05](../modules/06_rag/05_grounded_answers/theory.md) | Found/missed/absent/stale/conflict/protected в одной семье | Trace, таблица шести случаев, связь citation→chunk→source | [`rag-citation-validation`](../modules/06_rag/05_grounded_answers/exercises/citation_validation/README.md); найти unsupported claim | Различить ссылку и поддержку; локальные тесты подтверждают конкретные gates, не безопасность модели |
| Retrieval и answer evaluation, диагностика | [RAG 06](../modules/06_rag/06_rag_evaluation/theory.md) | Macro Recall@1=(1+0)/2=0.5 на двух размеченных запросах | Таблица причин ошибок; search/RAG/fine-tuning | `rag-retrieval-evaluation`, `rag-retrieval-regression`, `rag-ranking-study` по ссылкам урока | Обосновать единицу, ties, дубликаты, no-positive policy и held-out; ответы ученика требуют review |

Материалы читаются в прежнем порядке Module 05 → Module 06. HF/attention
пакета 5 переиспользуется ссылками; `training` не становится зависимостью модулей.
Новые author tests лежат вне прежних student targets; новые объяснения не меняют progress.
Следующее углубление **Agents/workflows и Production AI — PLANNED**.
Статусы [будущих лабораторных](ai-ml-extension-plan.md), в том числе real RAG,
не повышаются из-за локальной механической проверки.

<a id="theory-packet-7"></a>

## Теоретический пакет 7 — Agents/workflows и Production AI

Дата: 04.10.2026. Раздел дополняет историю выше; прежняя отметка пакета 7
как PLANNED описывает состояние до этой итерации. Здесь углубляются уже
существующие Module 07 и Module 08, без новых ID или live-лабораторных.
Команды, фактические результаты и границы — в [отчёте пакета](theory-packet-7-verification.md).
Понимание ученика **НЕ ПРОВЕРЕНО**.

### Аудит и переиспользование

В Module 07 уже были immutable state, отдельный visibility example, bounded
stop condition, approval digest, настоящие локальные LangGraph/MCP examples
и восемь самостоятельных заданий. Не хватало связного наблюдаемого перехода
от предложения к проверке, подтверждению, ошибке и восстановлению. Новая теория
связывает эти механизмы; прежние interfaces и generic student TODO не заменены.

В Module 08 уже были FastAPI lifespan/TestClient, release manifest, trace spans,
deadline calculation, trusted principal и rollback compatibility. Не хватало
единого разбора версии, окна telemetry, неизвестного качества и решения о выпуске.
Старые примеры и самостоятельный `production-product-study` сохраняются;
backend, preprocessing и LLM/RAG используются по ссылкам, а не переписываются.

### Пять свидетельств покрытия Agents/workflows

| Тема | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Последовательность, workflow, agent; состояние | [Agents 01](../modules/07_agents/01_workflows_state/theory.md) | Справочник велосервиса G-01 и проект напоминания | Переходы и таблица до/событие/проверка/после | [`agents-workflow-schedule`](../modules/07_agents/exercises/workflow_schedule/README.md), `agents-plan-validation` | Объяснить, когда фиксированный workflow достаточен; назвать владельца каждого решения |
| Tool call, schema, values, permission, approval | [Agents 02](../modules/07_agents/02_tools_permissions/theory.md) | Разрешённый вызов и отказ до имитации действия | Последовательность проверок | [`agents-tool-dispatch`](../modules/07_agents/02_tools_permissions/exercises/tool_dispatch/README.md) | Найти границу доверия, предложить проверку изменённых аргументов |
| Retry, idempotency, limits и unknown outcome | [Agents 03](../modules/07_agents/03_bounded_agents/theory.md) | Ошибка до действия против потерянного ответа после действия | Две трассы и счётчики | [`agents-bounded-loop`](../modules/07_agents/03_bounded_agents/exercises/bounded_loop/README.md), `agents-tool-result-routing` | Обосновать повтор или reconciliation; отмена ожидания не отменяет эффект |
| Checkpoint, resume, подтверждение и replay | [Agents 04](../modules/07_agents/04_checkpoints_approvals/theory.md) | JSON checkpoint ограниченного сценария и известный receipt | Сохранённые поля и возобновление | [`agents-checkpoint-resume`](../modules/07_agents/04_checkpoints_approvals/exercises/checkpoint_resume/README.md) | Предсказать последствия смены версии/call/args; объяснить предел локального replay |
| LangGraph и MCP | [Agents 05](../modules/07_agents/05_langgraph_mcp/theory.md) | Прежний настоящий локальный framework/SDK example | State→nodes→edges; client/server/tool | Старый `agents-langgraph-mcp`, без нового ID | Различить orchestration, protocol, discoverability и authorization |
| Goal, correctness, action policy, recovery | [Agents 06](../modules/07_agents/06_evaluation_handoffs/theory.md) | Семья случаев [walkthrough](../modules/07_agents/walkthrough.py), не trace настоящей LLM | Матрица исходов и наблюдаемые события | [`agents-trace-evaluation`](../modules/07_agents/06_evaluation_handoffs/exercises/trace_evaluation/README.md), `agents-handoff-packet` | Раздельно оценить полезность, допустимость и лимиты; ручная защита остаётся отдельной |

### Пять свидетельств покрытия Production AI

| Тема | Объяснение | Разобранный пример | Визуальная опора | Самостоятельная задача | Проверка понимания |
| --- | --- | --- | --- | --- | --- |
| Batch/online, contract, lifecycle, admission | [Production 01](../modules/08_production_ai/01_serving_contracts/theory.md) | Связанный workflow и прежний in-process serving example | Граница приложения и lifecycle | Старый `production-serving`, вариация перегруженной очереди | Отличить alive/ready/HTTP success/полезный результат; это не deployment |
| Release identity, preprocessing, evaluation | [Production 02](../modules/08_production_ai/02_releases_evaluation/theory.md) | Scripted release и заранее фиксированный протокол сравнения | Classifier/RAG поля; таблица кандидатов | [`production-release-gate`](../modules/08_production_ai/02_releases_evaluation/exercises/release_gate/README.md), `production-artifact-manifest` | Объяснить reject/hold и условность полей; hash не доказывает доверенность |
| Logs/metrics/traces и неизвестное качество | [Production 03](../modules/08_production_ai/03_observability/theory.md) | Окно синтетических запросов из того же сценария | Исходные записи, знаменатели, распределение задержек | [`production-request-metrics`](../modules/08_production_ai/exercises/request_metrics/README.md), `production-error-budget` | Пересчитать числа; не усреднять p95 групп и не считать missing labels успехом |
| Budgets, deadlines, очередь и повторы | [Production 04](../modules/08_production_ai/04_budgets_resilience/theory.md) | Учебные credits, прежний remaining timeout, unknown outcome из А | Таблица ресурсов и точек отказа | [`production-budget-reservation`](../modules/08_production_ai/04_budgets_resilience/exercises/budget_reservation/README.md) | Разделить резерв, расход, возврат и отмену; назвать недоказанные remote guarantees |
| Privacy, delayed feedback, drift/schema | [Production 05](../modules/08_production_ai/05_privacy_security/theory.md) | Минимальные события и сигналы, требующие расследования | Границы данных и виды изменений | [`production-redact-events`](../modules/08_production_ai/05_privacy_security/exercises/redact_events/README.md), `production-retention-policy` | Предложить различающее измерение; input drift сам по себе не доказывает падение качества |
| Canary/shadow, rollback, incident | [Production 06](../modules/08_production_ai/06_rollout_incidents/theory.md) | Более быстрый, но ошибочный кандидат; короткий инцидент | Exposure-схемы и timeline восстановления | [`production-rollout-decision`](../modules/08_production_ai/06_rollout_incidents/exercises/rollout_decision/README.md), затем `production-product-study` | Защитить решение при нехватке меток/несовместимой схеме; тест JSON не оценивает аргументацию |

### Последовательность и границы

После пакета 6: [Module 07](../modules/07_agents/README.md), уроки 01–06,
прогнозы → teacher walkthrough → собственные прежние задания. Затем
[Module 08](../modules/08_production_ai/README.md), уроки 01–06 и связанная
производственная демонстрация → самостоятельные policies/исследование.
Prerequisites и порядок старого маршрута не меняются. Учительские результаты
живут отдельно от submissions; `test/check` и progress остаются ученическими.

Реальные [RAG](../labs/03_real_rag/README.md),
[serving](../labs/05_model_serving/README.md),
[tracking/lifecycle](../labs/06_ml_lifecycle/README.md) и
[Document Intelligence](../projects/document_intelligence_lab/README.md)
сохраняют **PLANNED**. Уже запланированный [PEFT/LoRA](../labs/04_llm_finetuning/README.md)
остаётся отдельной веткой **ML-DEPTH · PLANNED**, а не обязательным условием
RAG или serving; QLoRA требует отдельной проверки совместимости.
Следующий пакет автоматически не начинается. Unit/in-process evidence не
удостоверяет качество настоящей модели, распределённую надёжность или deployment.

<a id="route-integration-audit"></a>

## Ограниченная интеграционная приёмка маршрута — 04.10.2026

Рабочая копия `C:\ProjectsDirectory\AIML\_road`, ветка `codex/ai-ml-wave1`,
HEAD `836028944eceaa260cb47d0056b593af4a4648d4`. Это выборочная проверка связности
после пакетов 1–7, **не** пакет 8 и не подтверждение качества всего курса.
Прочитаны отчёты, но выводы ниже сверены с самими README, theory, examples,
контрактами и реальными запусками. Предыдущие записи выше — история их итераций;
старое PLANNED там не отменяет последующее фактическое выполнение пакета.

### Маршрут и конкретные исправления

- Единый вход — [корневой README](../README.md). В нём, [setup](setup.md) и
  [Environment](../modules/01_python_core/00_environment/README.md) восстановлена
  цепочка Environment → Object Model → Collections **до** первого упражнения.
  В [detect duplicates](../modules/01_python_core/02_collections/exercises/detect_duplicates/README.md)
  пояснён one-shot generator: будущий урок 07 не стал новым prerequisite.
- [Module 04](../modules/04_machine_learning/README.md) больше не требует весь
  backend перед первым ML-опытом; нужны Python/data foundations. Убрано устаревшее
  утверждение, что готовая теория PyTorch/HF ещё PLANNED.
- В [roadmap](roadmap.md) будущий real RAG не блокирует локальную цепочку
  LLM/RAG → workflows → эксплуатационные основы. Backend остаётся параллельной
  веткой и нужен при переходе к serving; HF-ссылка не добавляет `training`
  базовым Modules 05–08.
- В [Data Foundations](../modules/03_data_foundations/README.md) явно отделена
  opt-in графическая практика: можно продолжить числовую статистику без Matplotlib.
- [Python testing](../modules/01_python_core/09_testing/README.md) теперь различает
  запуск `main()` и команду pytest для трёх существующих параметризованных случаев.
- В пяти авторских plot tests (четыре файла EDA/statistics/descent/classical)
  добавлен явный `plt.switch_backend("Agg")`: позднее изменение `MPLBACKEND`
  не переключало уже импортированный Matplotlib. Смешанный прогон воспроизвёл
  Tk/Tcl failure; проверки данных/осей/подписей и optional skips не ослаблены.
  Код демонстраций, CLI и learner targets не изменялись.

Каталог: **162 уникальных ID** (57 lessons, 102 exercises, 2 labs, 1 project),
все зарегистрированные README/tests существуют. В 162 README распознаны
48 явных prerequisite-блоков, из них сопоставлены 70 ID/link-связей:
неизвестных ID, битых целей и циклов в этих связях нет. Отдельно проверены
14 строк prerequisites второй волны. **Ограничение:** в curriculum нет поля
prerequisites; свободный текст вне распознанных блоков и неявный порядок уроков
не образуют автоматически проверенный полный DAG. Основной переход
Python → NumPy/Pandas → статистика → классическое ML → мост → PyTorch → HF
→ LLM/RAG → workflows → эксплуатация дополнительно прочитан вручную.

### Достаточное покрытие и конкретные пробелы

Существующие [итераторы](../modules/01_python_core/07_iterators_generators/README.md),
[декораторы](../modules/01_python_core/08_decorators/README.md),
[async](../modules/01_python_core/10_asyncio/README.md),
[FastAPI](../modules/02_python_backend/01_fastapi/README.md) и
[композиция зависимостей](../modules/02_python_backend/03_architecture_dependencies/README.md)
имеют объяснение, исполняемый пример, отдельный контракт задачи и вопросы.
Переиспользуются; отсутствие отдельного theory/SVG не признано недостатком.
По основному ядру сохранены пять видов свидетельств в таблицах пакетов выше;
выборочно сверены прогнозы, расчёты, самостоятельные вариации и границы `check`.

Ниже **NEEDS_DEPTH · PLANNED**, не реализовано при приёмке. Это конкретные
переходы к заданиям, а не утверждение, что соответствующей темы вообще нет.

| Материал / существующая задача | Чего не хватает перед задачей | Минимальное последующее дополнение |
| --- | --- | --- |
| [Python 05](../modules/01_python_core/05_data_modeling/README.md), `python-payment-model` | Пример создаёт frozen dataclass, но не разбирает `__post_init__` и проверку конечного Decimal/ASCII currency, требуемую задачей | Один другой value object: создание → проверка → отказ, без реализации payment TODO |
| [Python 06](../modules/01_python_core/06_exceptions_io/README.md), `python-json-export` | Чтение JSON/узкий except показаны; сохранность destination и очистка временного файла при двух фазах ошибки только названы | Небольшая временная схема serialization/replace/failure/cleanup, не готовый exporter |
| [Python 09](../modules/01_python_core/09_testing/README.md), `python-mock-provider` | Готовые parametrized/mock tests есть, но задача заполняет реализацию, а не проверяет самостоятельное проектирование теста | Ручная вариация выбора случаев и написания теста к иному поведению; старый check её не засчитывает |
| [Backend 02](../modules/02_python_backend/02_pydantic/README.md), `backend-transaction-contract` | Есть `Field` и объяснение error location, но нет разобранного `field_validator`, нужного контракту | Один отдельный валидатор с входом и наблюдаемым `loc`, не решение transaction contract |
| [Backend 06](../modules/02_python_backend/06_sqlalchemy/README.md), `backend-transaction-repository` | Session/commit/rollback/close перечислены, example описан словами; нет исполненного жизненного цикла сессии перед реализацией repository | Малый отдельный SQLite session trace с успешным/ошибочным исходом |
| [Backend 08](../modules/02_python_backend/08_api_integration_testing/README.md), `backend-api-test-review` | Изоляция двух app показана; правильный lifecycle yield-fixture и очистка overrides не разобраны до намеренно плохой fixture | Короткий корректный разбор setup → yield → teardown на другом route |

Эти пробелы не мешают первой сессии Object Model/Collections. Перед перечисленными
заданиями новичку понадобится дополнительное объяснение/помощь; приёмка не
объявляет их полное педагогическое покрытие. Новых обязательных ID не вводится.

### Свежие технические свидетельства и ограничения

Использованы существующие `.venv` (без torch/transformers/matplotlib) и
`.venv-training` (torch 2.14.0+cpu, transformers 5.17.0, datasets 5.0.1,
matplotlib 3.11.2), Python 3.12.14. Для каждой среды выполнен
`uv sync --locked --offline --dry-run` с соответствующим
`UV_PROJECT_ENVIRONMENT`; у второй также `--group training --group visualization`.
Результат: 156/193 packages checked, **Would make no changes**. Установка не
выполнялась; ни чистый install, ни пустой кеш этим не проверены.

| Реальная команда из корня | Результат |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q` | 1022 passed, 50 skipped, 1160 xfailed, 1 прежний warning, 104.49 s |
| `.venv-training/Scripts/python.exe -m pytest -q -rs` | 1129 passed, 6 skipped, 1224 xfailed, 1 прежний warning, 159.28 s |
| `.venv-training/Scripts/python.exe -m pytest labs modules/03_data_foundations/tests/test_eda_demo.py modules/03_data_foundations/tests/test_statistics_demo.py modules/04_machine_learning/tests/test_descent_demo.py modules/04_machine_learning/tests/test_classical_demo.py -q -rs` | До правки: 1 failed, 150 passed, 68 xfailed; после: 151 passed, 68 xfailed, 43.51 s |
| `.venv/Scripts/python.exe -m pytest modules/01_python_core/09_testing/example.py -q` | 3 passed |
| `.venv/Scripts/python.exe -m ruff check .` | All checks passed |
| `.venv/Scripts/python.exe -m ruff format --check .` | 859 files already formatted |
| `.venv/Scripts/python.exe -m mypy --show-traceback` | Success, 631 source files |
| `.venv/Scripts/python.exe -m mypy --no-incremental --cache-dir generated-reports/route-integration-audit/mypy-base` | Success, 631 source files, отдельный новый кеш |
| `.venv-training/Scripts/python.exe -m mypy -p labs` | Success, 52 source files |
| `git diff --check` | Exit 0 |

Первый обычный `mypy` сообщил INTERNAL ERROR 2.3.1, поэтому не засчитан как успех.
Повтор с traceback и полный неинкрементальный анализ выше прошли; точная причина
первого внутреннего сбоя не установлена, зависимости/правила типов не менялись.
В обеих регрессиях сохранён прежний Starlette/AnyIO DeprecationWarning.
Шесть training skips: две проверки Windows symlink без нужных прав и четыре
PostgreSQL без сервиса. В base дополнительно отсутствуют opt-in библиотеки.
Xfail по-прежнему означает незавершённую student boundary, не выполненное задание.

Дополнительный контролируемый запуск пяти plot tests после предварительного
`matplotlib.use('svg')` дал **5 passed**, конечный backend **Agg**. Это проверка
независимости от раннего импорта; Tcl/GPU/новые зависимости не устанавливались.

Примеры CLI (реальные результаты, не зачёт ученика): `test python-word-index`
→ exit 0/13 xfailed, `check` того же ID → exit 1; `check lab-pytorch` в base
→ exit 2/missing torch. В training `test lab-pytorch` → 19 passed/14 xfailed,
exit 0; `check` → exit 1. `test data-weather-quality` → 1 passed/21 xfailed,
exit 0; `check` → exit 1. Префикс команд — выбранный interpreter и
`scripts/learn.py`. EDA-продолжение не входит в weather target; продолжения
labs имеют отдельные targets. Преподавательские outputs не создают learner report.

Из корня реально выполнены 13 команд демонстраций: environment/Object Model,
NumPy walkthrough, Pandas example, stats_demo, descent_demo, classical_demo,
PyTorch/HF walkthrough с `--plots`, LLM/RAG/workflow/production walkthrough.
Все exit 0, новые выходы только в `generated-reports/route-integration-audit/demos-verified/`.
Точные argv и последовательность сохранены в локальном игнорируемом
`generated-reports/route-integration-audit/run_examples.py`; это одноразовый QA,
не дополнительный runner курса и не файл, доступный после нового clone.
Ранний запуск QA прервался на кодировке его журнала Windows, не на примере;
повтор использовал ASCII-safe JSON и новый каталог, старые outputs сохранены.

Проверка Markdown: **267** tracked/untracked документов — существование локальных
целей; **21** выбранный документ — 492 локальные ссылки, 28 якорей, 48 таблиц,
fences, 14 image alt и 7 SVG XML. Команда локального QA:
`.venv/Scripts/python.exe generated-reports/route-integration-audit/check_materials.py`.
Renderer **Mistune 3.3.4**, HTML разбирался в памяти. Object Model/NumPy SVG
содержат title/description и текстовые версии в теории; их числа/связи сверены
с запуском. PNG просмотрены средством просмотра изображений Codex:
statistics `sampling.png`, classical `decisions.png`, свежие PyTorch `learning.png`
и HF `attention.png`. Подписи/оси/легенды читаемы, числа согласованы с traces/tests.
Браузер запретил локальный `file:` URL: визуальный Markdown/SVG просмотр в этой
приёмке **NOT_RUN**; это не проверка GitHub или PyCharm rendering. Внешние URL
повторно не проверялись, веб-приложение/сервер не создавался.

Сверка SHA-256 **902** исходных tracked/untracked файлов: изменены только
13 файлов приёмки (восемь навигационных README/setup/roadmap, эта карта и четыре
авторских test-файла), остальные **889** побайтно прежние. Новых неигнорируемых
файлов и удалений нет. Отдельно совпали все **259** прежних файлов в reports/
generated-reports/ (runtime pycache исключён); новые teacher outputs отделены.
Student TODO/реализации, curriculum, CLI, зависимости/lock и progress сохранены.
SHA-256 `progress.md` — `9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.
Независимое read-only review узких изменений не обнаружило открытых замечаний;
полные suite и сверка сохранности выполнены контроллером, не рецензентом.
HEAD/ветка прежние; commit/push/merge и сетевых загрузок нет.
Число tests не доказывает понятность материала ученику.

### Первая сессия и остановка

Откройте [Environment](../modules/01_python_core/00_environment/README.md), затем
[Object Model](../modules/01_python_core/01_object_model/README.md): прогноз связей
имён → объяснение → запуск `example.py` → новая вариация → вопросы. После этого
Collections и первое упражнение; не пытайтесь сразу закрыть весь каталог.
В существующей среде из корня:

```powershell
.venv/Scripts/python.exe scripts/learn.py validate-env
.venv/Scripts/python.exe modules/01_python_core/01_object_model/example.py
```

Самостоятельное понимание/защита — **REQUIRES_REVIEW**. Real RAG, tracking,
PEFT/fine-tuning, serving/lifecycle и Document Intelligence остаются **PLANNED**
по [существующему плану](ai-ml-extension-plan.md). Pretrained/GPU/live/deployment,
PostgreSQL без сервиса и иные ОС не проверялись. Приёмка не запускает дальнейшее
расширение: оно требует отдельной задачи.
