# Wave 2: фактическое покрытие и недублирующие расширения

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
