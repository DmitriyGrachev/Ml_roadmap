# Wave 2: журнал фактической проверки

Обновлено: **01.10.2026**. Материалы Tasks 1–12 подготовлены; общий независимый
review завершён с вердиктом **With fixes**. Единый пакет F1–F8 исправлен и проверен
ниже; независимый scoped re-review **01.10.2026 завершён: F1–F8 ADDRESSED,
новых нарушений нет; материалы и инфраструктура готовы к передаче пользователю**.
**READY относится к материалам; VERIFIED — только к перечисленным техническим
проверкам в данной среде.** Ученические TODO не решались, progress не
отмечался, его эксперименты остаются NOT_RUN, содержательная защита REQUIRES_REVIEW.

## Финальный пакет F1–F8: фактическая проверка 01.10.2026

Проверены невырожденные seeded bootstrap bounds и число resamples, свежий
tabular output до выдачи доверия model.pkl, побайтная связь с неизменным входным
dataset, дополнительные malformed attention inputs, повторяемость всех candidate
артефактов и точные test IDs, наблюдаемая SQL tie variation и connect_ex во всех
11 offline fixtures. Малый sensor пример теперь показывает RF averaging и
последовательные boosting stages; обязательная самостоятельная вариация и её
защита описаны в прежнем models lesson и tabular package. Новых ID/зависимостей нет.

Отрицательные проверки сначала воспроизвели пропуски: degenerate-bootstrap mutant,
перенаправленный output/model path, подмена входа, одинаковые metrics при разных
артефактах, opposite SQL tie и два пропущенных connect_ex guards. После исправления
focused base: **88 passed, 17 xfailed**; attention: **2 passed, 22 xfailed**.
Это инфраструктурные регрессии; готовые learner решения не добавлялись.

| Свежий gate | Результат |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q -rs` | **924 passed, 39 skipped, 1160 xfailed**, 1 warning; exit 0; 71.55 s |
| `.venv-training/Scripts/python.exe -m pytest -q -rs` | **1011 passed, 6 skipped, 1224 xfailed**, 1 warning; exit 0; 97.75 s |
| Ruff check / format | exit 0; **780 files already formatted** |
| Base mypy / training mypy -p labs | exit 0; **608 / 48 source files**, no issues |
| Catalog/documentation/tracked links pytest | **39 passed, 1 skipped**; exit 0 |
| Дополнительный аудит всех tracked + untracked Markdown | **214 документов, 0 broken local links** |
| Сохранность | **88/88** protected files, **675/675** исходного snapshot и прежний checkpoint неизменны |

В full suites сохранены прежние Windows symlink/PostgreSQL/optional-training skips
и Starlette/AnyIO warning; пояснения ниже остаются в силе. Реальные locked installs
выполнены ранее (см. историю среды ниже); неизменные установки повторно не запускались.
Файлов по-прежнему **806 = 675 исходных + 131 новых**, 26 исходных изменены за всю
волну, удалённых 0. В final fix изменены 17 существующих файлов относительно
reviewed-final; перечень новых файлов ниже не расширился.

Обе команды `scripts/learn.py test ID` и `check ID` повторно выполнены для этих ID:

| ID | Среда | passed / xfailed |
| --- | --- | --- |
| data-paired-model-comparison | base | 9 / 12 |
| ml-tabular-study | base | 55 / 2 |
| ml-evaluation-case | base | 33 / 2 |
| backend-analytics-sql | base | 2 / 3 |
| data-release-study | base | 30 / 5 |
| ml-models | base | 2 / 13 |
| lab-attention-mechanics | training | 2 / 22 |

Во всех семи случаях **test exit 0**, **check exit 1 / CHECK INCOMPLETE**, skips 0.
Ни xfail, ни smoke, ни replay не доказывают авторство, качество learner experiment
или успешную ручную защиту. Pending scoped review не объявляется пройденным заранее.

Ниже сохранена история интеграционных запусков 30.09.2026, включая прежние сбои.

## Объём и навигация

Каталог: **162 ID = 57 lessons + 102 exercises + 2 labs + 1 project**.
Сохранены 148 прежних ID; добавлены ровно 14 exercise ID.
[Карта покрытия](wave2-coverage.md) содержит все README и prerequisites,
[маршрут](roadmap.md) объясняет порядок core → четыре контроля → боковые
ranking/forecasting branches. [Шаблон защиты](project-defense.md) общий.

В Task 1 targets двух прежних labs намеренно заменены с родительского каталога
на те же три старых файла каждой lab: PyTorch test_example/test_starter/test_report,
HF test_example/test_starter/test_protocol. Это сохраняет прежний объём зачёта
при появлении nested continuations. Остальные 146 прежних записей каталога
полностью совпадают с исходной копией. Новые ID имеют точные test-файлы,
собственный test_starter и required evidence/example/smoke tests.
Только три новых lab continuation имеют requires_training=true.

Новые ID и результаты обеих команд интеграционного прогона 30.09.2026:

| ID | Среда | passed / xfailed |
| --- | --- | --- |
| data-paired-model-comparison | base | 7 / 12 |
| data-randomized-experiment | base | 1 / 8 |
| ml-knn-mechanics | base | 2 / 23 |
| ml-tabular-study | base | 49 / 2 |
| lab-training-resume | training | 19 / 19 |
| lab-training-diagnostics | training | 43 / 4 |
| lab-attention-mechanics | training | 2 / 10 |
| data-release-study | base | 30 / 5 |
| ml-evaluation-case | base | 29 / 2 |
| production-product-study | base | 25 / 2 |
| rag-ranking-study | base | 17 / 2 |
| ml-forecasting-intro | base | 25 / 9 |
| python-interview-patterns | base | 2 / 18 |
| backend-analytics-sql | base | 1 / 3 |

Для **каждой** строки реально запущены scripts/learn.py test ID и check ID:
test вернул **0**, check — **1 / CHECK INCOMPLETE**. Skips в этих selected runs — 0.
Shared evidence tests входят в несколько ID; суммы строк не являются числом
уникальных тестов. Зелёный test не выдаёт зачёт незавершённым TODO.

## Среда и реальные установки

Windows, PowerShell, Python **3.12.14**, pytest **9.1.1**.
Рабочая копия C:\ProjectsDirectory\AIML\_road, ветка codex/ai-ml-wave1,
HEAD 03a729bc3952df39793d8ccbdbbf64b08d6a123f. Проверялась существующая dirty
копия; исходные изменения первой волны сохранены. Сравнение выполнено с
pre-wave snapshot, а не только с HEAD.

Реально выполнены **без --check**:

~~~powershell
uv sync --locked
$env:UV_PROJECT_ENVIRONMENT = "C:/ProjectsDirectory/AIML/_road/.venv-training"
uv sync --locked --group training
~~~

Base: **192 resolved / 156 checked**, exit 0; training: **192 resolved /
186 checked**, exit 0. Среды уже были установлены и синхронизированы: эти
команды проверили/применили locked sync, новых wheels не понадобилось.
Это не эксперимент с установкой с пустого cache. Lockfile и pyproject не изменялись.

Distribution metadata: base **не содержит torch, transformers, datasets**;
training содержит **torch 2.14.0+cpu, transformers 5.17.0, datasets 5.0.1**.
В обеих средах NumPy **2.5.3**, scikit-learn **1.9.1**.
torch.version.cuda = None, torch.cuda.is_available() = False.
Локальная папка datasets не является установленной HF distribution.

## История интеграционных gates 30.09.2026

Все команды выполнены из корня репозитория. Для полных прогонов установлены
HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, HF_DATASETS_OFFLINE=1.
Суффикс -rs только показывает причины skip; paths не исключались.

| Проверка | Фактическая команда | Результат |
| --- | --- | --- |
| Полная база | .venv/Scripts/python.exe -m pytest -q -rs | **911 passed, 39 skipped, 1160 xfailed**, 1 warning; exit 0; 77.62 s |
| Полный training | .venv-training/Scripts/python.exe -m pytest -q -rs | **998 passed, 6 skipped, 1212 xfailed**, 1 warning; exit 0; 102.57 s |
| Ruff | .venv/Scripts/python.exe -m ruff check . | All checks passed; exit 0 |
| Format | .venv/Scripts/python.exe -m ruff format --check . | **780 files already formatted**; exit 0 |
| Base types | .venv/Scripts/python.exe -m mypy | **608 source files**, no issues; exit 0 |
| Training types | .venv-training/Scripts/python.exe -m mypy -p labs | **48 source files**, no issues; exit 0 |
| Strict isolation | .venv/Scripts/python.exe -m pytest tests/tooling/test_check.py -q | **20 passed**; exit 0; 18.72 s |
| Tooling/docs/links | .venv/Scripts/python.exe -m pytest tests/tooling/test_check.py tests/tooling/test_catalog.py tests/tooling/test_cli.py tests/tooling/test_documentation.py tests/integration/test_markdown_links.py -q | **67 passed, 1 skipped**; exit 0 |
| Network fixtures | .venv/Scripts/python.exe -m pytest tests/integration/test_catalog_contracts.py -q -k block_network | **11 passed, 5 deselected**; exit 0 |
| Environment | .venv/Scripts/python.exe scripts/learn.py validate-env | Python/uv/interpreter found; exit 0 |
| Первый lesson | .venv/Scripts/python.exe scripts/learn.py test python-environment | **31 passed**; exit 0 |
| Checkpoint I/O smoke | .venv-training/Scripts/python.exe -m pytest labs/01_pytorch_foundations/exercises/resume_training/test_smoke.py -q | **7 passed**; exit 0 |
| Whitespace | git diff --check | exit 0 |
| Все tracked + untracked Markdown | existing broken_local_links по git ls-files --cached --others --exclude-standard | **214 файлов, 0 broken local links** |
| Финальный документ/catalog/link recheck после записи отчёта | .venv/Scripts/python.exe -m pytest tests/tooling/test_documentation.py tests/integration/test_catalog_contracts.py tests/integration/test_markdown_links.py -q | **29 passed**; exit 0 |

Strict fixtures доказывают успешный check законченного isolated target при
незавершённых соседних заданиях; отдельный continuation не расширяет старую lab.
Required xfail, skip, collection skip, пустой target, скрывающие collection
опции и отсутствующее required evidence дают отказ. Optional live/GPU tests
не выдаются за обязательные выполненные проверки. Ручная защита остаётся отдельной.
Отдельный реальный check lab-training-resume в base вернул **2** до запуска tests:
torch отсутствует, показана подсказка установки. Это ошибка доступности среды,
в отличие от **1 / incomplete** для того же ID в training с незавершённым TODO.

Два skip в обеих средах — Windows WinError 1314/невозможность создать directory
и file symlink (test_catalog.py и test_experiment_evidence.py).
Ещё четыре — не настроенный ROADMAP_POSTGRES_URL: postgres_query и три Banking
AI Lab integration cases. В базе дополнительно 33 optional-training skip.
Ни один из них не засчитан как успешный lab/PostgreSQL эксперимент.

Единственное предупреждение каждого полного прогона: Starlette TestClient
использует deprecated anyio.abc.BlockingPortal alias. Оно не подавлялось;
глобальные ignore/dependency updates не добавлялись.

### Обнаруженные и исправленные integration failures

Первый full base: 2 failed / 898 passed / 39 skipped / 1160 xfailed;
первый training: 1 failed / 986 passed / 6 skipped / 1212 xfailed.
Причина — введённая при интеграции ошибочная ссылка interview-defense.md вместо
project-defense.md: test_every_tracked_local_markdown_link_resolves и
test_shared_documentation_relative_links_resolve (последний только в первом base).
Ссылка исправлена; финальные полные прогоны выше выполнены после исправления.

Аудит выявил отсутствие deny-network fixtures у paired_model_comparison,
randomized_experiment, knn_mechanics, interview_patterns, analytics_sql.
Новая behavioral regression сначала дала **5 failed / 6 passed** на отсутствующих
guards, затем **11 passed** после пяти локальных conftest.py.
Probe запускает настоящую pytest fixture и требует отказа socket.create_connection
и socket.connect. Аргумент None не является адресом: даже при сломанном guard
реальное соединение не открывается. Новые guards блокируют также connect_ex.
Их добавление не меняет student code или CLI. Последние полные gates включают этот fix.

## Offline examples, smokes и границы свидетельств

До import/collection всех новых targets заблокированы socket.create_connection,
socket.socket.connect и connect_ex; установлены три HF offline flags.
Training pytest --collect-only по точным targets 14 новых ID:
**362 unique tests collected**, exit 0. Скачивания при collection не было.
Все 11 новых non-lab exercise paths имеют local autouse deny-network fixture;
три lab continuation наследуют labs/conftest.py.

Отдельные реальные малые запуски выполнены под тем же socket guard. Выходные
каталоги созданы через tempfile.mkdtemp вне репозитория; существующие learner
artifacts не перезаписывались. Выполнялись только доверенные примеры/fixtures
репозитория; произвольный Python из сохранённых learner artifacts не импортировался.

| Вызов под guard | Наблюдение | Что это НЕ доказывает |
| --- | --- | --- |
| paired_model_comparison.example.run_example() | effect -0.75, CI [-2.0, 0.5], 2 sensors, 200 resamples | освоение cluster bootstrap учеником |
| randomized_experiment.example.run_example() | 24 units × 3 events, A/A 0.14394898, A/B 0.54394898 | реальный causal effect или успешный A/B |
| knn_mechanics.example.run_example() | смена единиц меняет nearest row 0 → 1 | готовый learner kNN |
| forecasting_intro.example.previous_day_error() | 3.0 на четырёх температурах | temporal study/backtest ученика |
| tabular_study.example.run_sensor_lifecycle(new_dir, seed=11) | свежий sensor model save/reload, replayed=true, 8 probabilities | полный tabular experiment/calibration ученика |
| evaluation_case.candidate.run_candidate(new_dir) | 32 predictions, 32 correct, arithmetic accuracy=1.0 | достоверность оценки supplied candidate |
| data_release.generate.generate(new_dir, records=24, seed=23) | маленький synthetic fixture/provenance | готовый bounded-memory release ученика |
| attention_mechanics.example.run_example() | shape [1,2,3,4], finite; forbidden-token effects 0.0 | learner attention/gradient correctness |
| resume_training.fixture.fresh_run(new_path) | отдельный процесс, 7 continuous steps, epoch 1, offset 9 | completed learner capture/restore/resume |
| debugging.fixtures.run_case(case, new_dir, seed=57), a–d | trace lengths [8,1,8,8] | ученическое исправление четырёх случаев |

Дополнительно checkpoint I/O smoke проверяет scalar save/load, corrupt/unsafe
payload rejection, RNG bookkeeping и fresh subprocess. SQLite/interview fixtures,
ranking/product evidence и маленький generator покрыты full suite/selected IDs;
у этих пакетов нет отдельной готовой learner solution для демонстрации успеха.

Фактические временные roots: wave2-final-base-87g0lxe4,
wave2-final-training-i8doartd, wave2-final-data-r3_00ruy в Windows Temp.
Это mechanical evidence. Ни accuracy supplied candidate, ни случайный encoder,
ни траектория fixture не являются заявкой на качество обученной учеником модели.

## Сохранность и полный inventory относительно начала волны

Baseline: **675 tracked/untracked nonignored files** в initial-hashes.json;
immutable initial/ проверен по всем 675 хешам, совпадения полные.
Это snapshot перед реализацией после трёх audit docs (ранний аудит считал 672).
Сейчас **806** nonignored files: **131 новый, 26 изменённых прежних, 0 удалений**.
Список ниже включает всю волну, не только Task 12; файлы первой волны,
которые уже существовали в baseline, не названы новыми.

Все **85 прежних starter.py** и остальные прежние student implementation files
сохранены побайтово: среди изменённых старых файлов только документы, catalog и
инфраструктурные tests. Защищённая группа **88 файлов**
(starters + progress + pyproject + uv.lock) совпадает целиком.
Progress SHA-256: 9c78d95d05efb7234c8b3412d072577916a11192531aee1b27a0df60ce647dc0.
Существующий generated-reports/pytorch/smoke/shape-smoke.pt совпадает с
learner-artifact-hashes.json:
713dbe951d99d8580fe34165041b525dc3ab43f2a46f547c5910a17d80276f16.

Tracked/untracked nonignored inventory не содержит новых .pt/.pth/.pkl/.joblib/
.safetensors/.pyc, environment/cache/generated-reports artifacts.
Для сохраняемых datasets/experiments предусмотрены ignored data/derived/,
derived-data/, artifacts/ и generated-reports/; фактические новые smoke outputs
этого прогона находятся в Windows Temp, не в произвольной папке datasets/.
малые учебные fixtures ниже включены намеренно. Secrets не добавлялись.
Staged diff пустой; branch и HEAD прежние. Commit/push/merge/stash/reset/clean,
удаление или переезд пользовательских файлов не выполнялись.

### Изменённые прежние файлы (26)

- `README.md`
- `curriculum.toml`
- `docs/ai-ml-extension-plan.md`
- `docs/compute-guide.md`
- `docs/experiment-protocol.md`
- `docs/roadmap-coverage-review.md`
- `docs/roadmap.md`
- `docs/skills-matrix.md`
- `docs/superpowers/plans/2026-09-30-ai-ml-wave2.md`
- `docs/testing-exercises.md`
- `docs/wave2-coverage.md`
- `docs/wave2-verification.md`
- `labs/01_pytorch_foundations/README.md`
- `labs/02_huggingface_models/README.md`
- `modules/01_python_core/00_environment/README.md`
- `modules/01_python_core/README.md`
- `modules/01_python_core/tests/test_learning_flow.py`
- `modules/02_python_backend/tests/test_lesson_contracts.py`
- `modules/03_data_foundations/04_practical_statistics/README.md`
- `modules/04_machine_learning/04_models/README.md`
- `modules/04_machine_learning/05_evaluation/README.md`
- `modules/04_machine_learning/07_training_bridge/README.md`
- `tests/integration/test_catalog_contracts.py`
- `tests/integration/test_repository_hygiene.py`
- `tests/tooling/test_check.py`
- `tests/tooling/test_documentation.py`

### Новые файлы (131)

- `docs/project-defense.md`
- `labs/01_pytorch_foundations/debugging/README.md`
- `labs/01_pytorch_foundations/debugging/__init__.py`
- `labs/01_pytorch_foundations/debugging/case_a.py`
- `labs/01_pytorch_foundations/debugging/case_b.py`
- `labs/01_pytorch_foundations/debugging/case_c.py`
- `labs/01_pytorch_foundations/debugging/case_d.py`
- `labs/01_pytorch_foundations/debugging/evidence.py`
- `labs/01_pytorch_foundations/debugging/fixtures.py`
- `labs/01_pytorch_foundations/debugging/starter.py`
- `labs/01_pytorch_foundations/debugging/test_cases.py`
- `labs/01_pytorch_foundations/debugging/test_evidence.py`
- `labs/01_pytorch_foundations/debugging/test_starter.py`
- `labs/01_pytorch_foundations/exercises/__init__.py`
- `labs/01_pytorch_foundations/exercises/resume_training/README.md`
- `labs/01_pytorch_foundations/exercises/resume_training/__init__.py`
- `labs/01_pytorch_foundations/exercises/resume_training/evidence.py`
- `labs/01_pytorch_foundations/exercises/resume_training/fixture.py`
- `labs/01_pytorch_foundations/exercises/resume_training/starter.py`
- `labs/01_pytorch_foundations/exercises/resume_training/test_evidence.py`
- `labs/01_pytorch_foundations/exercises/resume_training/test_smoke.py`
- `labs/01_pytorch_foundations/exercises/resume_training/test_starter.py`
- `labs/02_huggingface_models/attention_mechanics/README.md`
- `labs/02_huggingface_models/attention_mechanics/__init__.py`
- `labs/02_huggingface_models/attention_mechanics/example.py`
- `labs/02_huggingface_models/attention_mechanics/starter.py`
- `labs/02_huggingface_models/attention_mechanics/test_example.py`
- `labs/02_huggingface_models/attention_mechanics/test_starter.py`
- `modules/01_python_core/exercises/interview_patterns/README.md`
- `modules/01_python_core/exercises/interview_patterns/__init__.py`
- `modules/01_python_core/exercises/interview_patterns/conftest.py`
- `modules/01_python_core/exercises/interview_patterns/instrumentation.py`
- `modules/01_python_core/exercises/interview_patterns/starter.py`
- `modules/01_python_core/exercises/interview_patterns/test_instrumentation.py`
- `modules/01_python_core/exercises/interview_patterns/test_starter.py`
- `modules/02_python_backend/exercises/analytics_sql/README.md`
- `modules/02_python_backend/exercises/analytics_sql/__init__.py`
- `modules/02_python_backend/exercises/analytics_sql/conftest.py`
- `modules/02_python_backend/exercises/analytics_sql/fixtures.py`
- `modules/02_python_backend/exercises/analytics_sql/starter.py`
- `modules/02_python_backend/exercises/analytics_sql/test_queries.py`
- `modules/02_python_backend/exercises/analytics_sql/test_starter.py`
- `modules/03_data_foundations/exercises/data_release/README.md`
- `modules/03_data_foundations/exercises/data_release/__init__.py`
- `modules/03_data_foundations/exercises/data_release/conftest.py`
- `modules/03_data_foundations/exercises/data_release/evidence.py`
- `modules/03_data_foundations/exercises/data_release/fixtures/labels.csv`
- `modules/03_data_foundations/exercises/data_release/fixtures/provenance.json`
- `modules/03_data_foundations/exercises/data_release/fixtures/source_a.csv`
- `modules/03_data_foundations/exercises/data_release/fixtures/source_b.jsonl`
- `modules/03_data_foundations/exercises/data_release/generate.py`
- `modules/03_data_foundations/exercises/data_release/starter.py`
- `modules/03_data_foundations/exercises/data_release/test_evidence.py`
- `modules/03_data_foundations/exercises/data_release/test_generate.py`
- `modules/03_data_foundations/exercises/data_release/test_starter.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/README.md`
- `modules/03_data_foundations/exercises/paired_model_comparison/__init__.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/conftest.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/evidence.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/example.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/starter.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/test_evidence.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/test_example.py`
- `modules/03_data_foundations/exercises/paired_model_comparison/test_starter.py`
- `modules/03_data_foundations/exercises/randomized_experiment/README.md`
- `modules/03_data_foundations/exercises/randomized_experiment/__init__.py`
- `modules/03_data_foundations/exercises/randomized_experiment/conftest.py`
- `modules/03_data_foundations/exercises/randomized_experiment/example.py`
- `modules/03_data_foundations/exercises/randomized_experiment/starter.py`
- `modules/03_data_foundations/exercises/randomized_experiment/test_example.py`
- `modules/03_data_foundations/exercises/randomized_experiment/test_starter.py`
- `modules/04_machine_learning/exercises/evaluation_case/README.md`
- `modules/04_machine_learning/exercises/evaluation_case/__init__.py`
- `modules/04_machine_learning/exercises/evaluation_case/candidate.py`
- `modules/04_machine_learning/exercises/evaluation_case/conftest.py`
- `modules/04_machine_learning/exercises/evaluation_case/evidence.py`
- `modules/04_machine_learning/exercises/evaluation_case/fixture.py`
- `modules/04_machine_learning/exercises/evaluation_case/starter.py`
- `modules/04_machine_learning/exercises/evaluation_case/test_case.py`
- `modules/04_machine_learning/exercises/evaluation_case/test_evidence.py`
- `modules/04_machine_learning/exercises/evaluation_case/test_starter.py`
- `modules/04_machine_learning/exercises/forecasting_intro/README.md`
- `modules/04_machine_learning/exercises/forecasting_intro/__init__.py`
- `modules/04_machine_learning/exercises/forecasting_intro/conftest.py`
- `modules/04_machine_learning/exercises/forecasting_intro/evidence.py`
- `modules/04_machine_learning/exercises/forecasting_intro/example.py`
- `modules/04_machine_learning/exercises/forecasting_intro/fixture.py`
- `modules/04_machine_learning/exercises/forecasting_intro/starter.py`
- `modules/04_machine_learning/exercises/forecasting_intro/test_evidence.py`
- `modules/04_machine_learning/exercises/forecasting_intro/test_example.py`
- `modules/04_machine_learning/exercises/forecasting_intro/test_starter.py`
- `modules/04_machine_learning/exercises/knn_mechanics/README.md`
- `modules/04_machine_learning/exercises/knn_mechanics/__init__.py`
- `modules/04_machine_learning/exercises/knn_mechanics/conftest.py`
- `modules/04_machine_learning/exercises/knn_mechanics/example.py`
- `modules/04_machine_learning/exercises/knn_mechanics/starter.py`
- `modules/04_machine_learning/exercises/knn_mechanics/test_example.py`
- `modules/04_machine_learning/exercises/knn_mechanics/test_starter.py`
- `modules/04_machine_learning/exercises/tabular_study/README.md`
- `modules/04_machine_learning/exercises/tabular_study/__init__.py`
- `modules/04_machine_learning/exercises/tabular_study/conftest.py`
- `modules/04_machine_learning/exercises/tabular_study/evidence.py`
- `modules/04_machine_learning/exercises/tabular_study/example.py`
- `modules/04_machine_learning/exercises/tabular_study/fixture.py`
- `modules/04_machine_learning/exercises/tabular_study/starter.py`
- `modules/04_machine_learning/exercises/tabular_study/test_evidence.py`
- `modules/04_machine_learning/exercises/tabular_study/test_example.py`
- `modules/04_machine_learning/exercises/tabular_study/test_starter.py`
- `modules/06_rag/exercises/ranking_study/README.md`
- `modules/06_rag/exercises/ranking_study/__init__.py`
- `modules/06_rag/exercises/ranking_study/conftest.py`
- `modules/06_rag/exercises/ranking_study/evidence.py`
- `modules/06_rag/exercises/ranking_study/fixtures/corpus.jsonl`
- `modules/06_rag/exercises/ranking_study/fixtures/judgments.json`
- `modules/06_rag/exercises/ranking_study/fixtures/queries.jsonl`
- `modules/06_rag/exercises/ranking_study/starter.py`
- `modules/06_rag/exercises/ranking_study/test_evidence.py`
- `modules/06_rag/exercises/ranking_study/test_starter.py`
- `modules/08_production_ai/exercises/product_study/README.md`
- `modules/08_production_ai/exercises/product_study/__init__.py`
- `modules/08_production_ai/exercises/product_study/conftest.py`
- `modules/08_production_ai/exercises/product_study/evidence.py`
- `modules/08_production_ai/exercises/product_study/fixtures/constraints.json`
- `modules/08_production_ai/exercises/product_study/fixtures/requests.jsonl`
- `modules/08_production_ai/exercises/product_study/starter.py`
- `modules/08_production_ai/exercises/product_study/test_evidence.py`
- `modules/08_production_ai/exercises/product_study/test_starter.py`
- `src/roadmap_tools/experiment_evidence.py`
- `src/roadmap_tools/open_control_evidence.py`
- `tests/tooling/test_experiment_evidence.py`
- `tests/tooling/test_open_control_evidence.py`

## Точные команды для продолжения обучения

Из PowerShell в корне проекта:

~~~powershell
uv sync --locked
.venv/Scripts/python.exe scripts/learn.py validate-env
.venv/Scripts/python.exe scripts/learn.py list
.venv/Scripts/python.exe scripts/learn.py test python-environment
.venv/Scripts/python.exe scripts/learn.py test data-paired-model-comparison
.venv/Scripts/python.exe scripts/learn.py check data-paired-model-comparison
~~~

Последние две команды подходят **после prerequisites из README**. До собственной
реализации check ожидаемо возвращает 1; это не ошибка установки. На старте Java/
Spring-инженер проходит Python object model/collections/functions/typing,
затем data/ML и training bridge. Не нужно завершать все восемь модулей до PyTorch.

Отдельный training interpreter:

~~~powershell
$env:UV_PROJECT_ENVIRONMENT = ".venv-training"
uv sync --locked --group training
Remove-Item Env:UV_PROJECT_ENVIRONMENT
.venv-training/Scripts/python.exe scripts/learn.py test lab-training-resume
.venv-training/Scripts/python.exe scripts/learn.py check lab-training-resume
.venv-training/Scripts/python.exe scripts/learn.py test lab-training-diagnostics
.venv-training/Scripts/python.exe scripts/learn.py test lab-attention-mechanics
~~~

Для любого другого ID таблицы используется тот же test/check и указанный
interpreter. PyCharm: working directory — корень; interpreter .venv для base,
.venv-training для labs. Исходная рекомендация uv sync --all-groups в первом
environment lesson заменена на uv sync --locked и ссылку на optional training.

## NOT_RUN и ручные границы

- Все реальные learner studies, repaired cases, attention/kNN implementations,
  resume capture/restore, reports и защита — не выполнены агентом.
- Содержательные provenance/split validity, bounded memory, algorithmic complexity,
  объяснения, ограничения и перенос на новую вариацию требуют REQUIRES_REVIEW.
  Проверенный JSON/hash не доказывает честный эксперимент или качество вывода.
- Большой data generator, pretrained weights/datasets, GPU/CUDA/Colab, cloud,
  PostgreSQL service и чистая установка с пустого cache — NOT_RUN.
- Старый PyTorch schema-1 report доказывает traceability/арифметику, не inference
  из snapshot; это явно сохранённая граница, не новая гарантия.
- Real RAG/vector DB, MLflow/tracking, SFT/LoRA/QLoRA, vLLM/serving,
  production lifecycle, Document Intelligence и глубокие специализации — PLANNED.
  Короткие ranking/forecasting intro READY не меняют эти статусы.
- Task reviews и общий broad review выполнены; broad review потребовал F1–F8.
  Независимый scoped re-review 01.10.2026 подтвердил: все F1–F8 ADDRESSED,
  новых нарушений нет; материалы и инфраструктура готовы к передаче пользователю
  с сохранением границ NOT_RUN / REQUIRES_REVIEW / PLANNED.
