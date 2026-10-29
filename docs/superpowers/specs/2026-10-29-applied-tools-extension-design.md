# Прикладные инструменты ML/NLP: расширение PA1

## Цель и разрешённый результат

Пользователь поручил добавить рекомендованную практику и расширить основные
инструменты, самостоятельно принять разумные решения, закоммитить и опубликовать
отдельную ветку **`namepfchekcoutbranch-extended-pa1`**. Его review происходит после
публикации. Основание — опубликованный `codex/ml-engineer-readiness`, commit
`2c75f94becc999975cc397bbf4013716b46d4568`. Новое согласование дизайна не требуется.

Аудит показал хорошую базу ручного PyTorch/Transformers, но слабый переход к
Trainer/Datasets, pretrained generative SFT, настоящему reranker, GPU memory
practice, NER и управлению собственными экспериментами. В основных инструментах
полезны NumPy с масками и батчами, признаки Pandas на момент события и подбор
sklearn pipeline без утечки. Учебная цель — самостоятельная Applied ML/NLP работа
для человека с Java/Spring, начинающего Python/ML; не инфраструктурный курс.

## Подход

Рассмотрены: только новые ссылки; большой набор самостоятельных технологий;
последовательные практикумы поверх существующих примеров. Выбран третий вариант:
он связывает конкретную задачу, объяснение, API и проверяемый результат. Это выбор
исполнителя в рамках явно делегированных пользователем решений.

Каждый новый блок включает русскую теорию с числовым/пошаговым примером, небольшой
авторский пример на соседней задаче, незаполненный learner starter, поведенческие
проверки, инструкции PyCharm/CLI, типичные ошибки и защиту. Сначала механика на
локальных малых данных; затем явно запускаемый опыт с локальным pretrained snapshot.
Маленькая random модель проверяет API и градиенты, но не языковое качество.

## Состав

1. NumPy masked/vectorized features, Pandas point-in-time features, sklearn
   ColumnTransformer/Pipeline/CV и inspection.
2. Hugging Face Trainer/Datasets/collator, best checkpoint/resume; NER/token
   classification с выравниванием subword labels и entity-level evaluation.
3. Pretrained SFT/LoRA: chat template, assistant/completion loss masks, baseline /
   prompt / adapter comparison, reload. Отдельная практика training efficiency:
   accumulation, GPU measurement/AMP и opt-in QLoRA.
4. Настоящий CrossEncoder reranker и адаптация embeddings с hard negatives,
   отдельной оценкой candidate recall/ranking и query-disjoint holdout.
5. MLflow для собственных экспериментов и bounded Optuna search на validation.
6. Учёт существующей vLLM lab через самостоятельный measurement/receipt контракт.
   Внешний сервер остаётся отдельным действием ученика.
7. Общая интеграция: каталог, progress, маршруты, dependency diagnostics,
   навигация и честный verification report.

DPO/GRPO, distillation, continued pretraining, CV и distributed training остаются
объяснёнными продолжениями по задаче; полноценные новые курсы этих специализаций
не нужны для текущей модели подготовки. Существующая обязательная vLLM цель
сохраняется, Linux/WSL runtime не подменяется MockTransport.

## Global Constraints

- Ветка `namepfchekcoutbranch-extended-pa1`; parent исходного изменения — `2c75f94becc999975cc397bbf4013716b46d4568`. Исходные ветки не меняются, merge/PR не выполняются.
- Существующие 180 catalog records и имеющиеся learner boundaries сохраняются; новые ID добавляются, progress не отмечается выполненным.
- Никаких скрытых network/download/training на import или обычном pytest. Pretrained loaders работают только с явным локальным snapshot; скачивание — отдельная документированная команда.
- Author demo, random model smoke, skip и xfail не дают learner credit. Строгий check требует learner implementation и заявленные артефакты; авторство/новый домен проверяются человеком.
- Не запускать полные pytest отдельно каждым агентом, повторные benchmarks, pretrained training, GPU, сервер или загрузку весов. Разрешены короткие scoped CPU/API tests и один интегрированный набор новых/затронутых tests; полный supported-platform прогон — в CI после публикации.
- Root единолично меняет общие catalog/tracks/progress/pyproject/uv.lock/CLI/CI и выполняет git commits. Агенты меняют только назначенные пути; setup зависимостей выполняет root.
- Base runtime остаётся CPU/offline. Optional группы: `trainer`, `sft`, `ranking`, `experiments`, `quantization`; отсутствие группы даёт понятную инструкцию и не засчитывается строгим check.
- Новые файлы имеют одну понятную ответственность; не создаётся общий framework экспериментов и не копируется общий validator между задачами без причины.
- В новой теории есть prerequisites, разбор вычисления/схемы данных, типичные ошибки и критерии переноса. Предпочитать Markdown/Mermaid и небольшие таблицы, не ASCII схемы и не изображения с выдуманными метриками.
- Learner функции остаются с прямым `NotImplementedError`; авторский пример не является готовой универсальной реализацией этих функций.
- Выходные артефакты создаются в новых каталогах, ограничены размером, не попадают в git; ошибка не выдаётся за успешный report. Результаты измерений и pretrained качество не выдумываются.

## Общие интерфейсы и владение

Каждый task report содержит точные ID, заголовок README, test targets и qualified
learner boundaries для регистрации root. `test_starter.py` использует существующий
`student_exercise`; тесты авторских инструментов не включаются в новые completion
targets. Необязательные библиотечные проверки используют importorskip в base,
но явный installed-group CI обязан выполнять их. Малые CPU fixtures используют
настоящую библиотеку, а не mocks, изображающие обучившуюся модель.

Новый необязательный catalog field `requires_groups` — tuple/list имён из фиксированного
набора поддерживаемых групп; `requires_training` сохраняет обратную совместимость.
CLI собирает объединение нужных групп и проверяет import availability без загрузки
framework. Для missing group выводит одну команду `uv sync --locked` со всеми
необходимыми группами, сохраняя `training`/`migrations` для полного track.

Для live submissions нужны собственный код, origin/revision/config, train/dev/test
identity, настоящие predictions, метрики, hashes и повторная загрузка модели.
Generic receipt может проверять структуру и арифметику, но качество/авторство не
объявляется автоматически доказанным. Каждый блок явно разделяет технический
зачёт, live результат и человеческую защиту.

## Проверка и публикация

Последний parent уже прошёл Ubuntu/Windows CI; повторять baseline не нужно.
Каждый implementer фиксирует targeted RED/GREEN для существенных новых контрактов,
затем scoped Ruff/mypy. Свежий reviewer проверяет scope по diff без повторения
уже выполненных тестов. Root один раз проверяет интеграцию и пакет новых API.
Один полный review итоговой ветки, затем публикация точного дерева и наблюдение
одного автоматического CI. При реальной обнаруженной ошибке — только необходимое
исправление и соответствующая проверка. Review пользователя следует после push.

## Первичные ориентиры

API сверяются с установленными закреплёнными версиями и официальными материалами:
[PyTorch](https://docs.pytorch.org/tutorials/beginner/basics/intro.html),
[Transformers Trainer](https://huggingface.co/docs/transformers/training),
[TRL SFT](https://huggingface.co/docs/trl/sft_trainer),
[PEFT quantization](https://huggingface.co/docs/peft/developer_guides/quantization),
[NER](https://huggingface.co/docs/transformers/tasks/token_classification),
[Sentence Transformers](https://www.sbert.net/docs/sentence_transformer/training_overview.html),
[CrossEncoder](https://www.sbert.net/docs/cross_encoder/usage/usage.html),
[Optuna](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/001_first.html).

Метаданные PyPI проверены 29.10.2026: accelerate 1.15.0, TRL 1.16.0,
Sentence Transformers 6.2.0, Optuna 5.0.0, bitsandbytes 0.50.2 совместимы по
заявленным ограничениям с закреплёнными torch 2.14 / transformers 5.17 / datasets 5.0.1.
Это предварительная проверка metadata; локальные API smoke и lock подтверждают
фактическую библиотечную интеграцию, GPU совместимость остаётся отдельным опытом.
