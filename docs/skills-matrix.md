# Аудит компетенций: первая волна

Это исторический аудит первой волны. Актуальное продолжение от 30.09.2026:
[14 упражнений второй волны и prerequisites](wave2-coverage.md),
[проверки инфраструктуры и границы NOT_RUN](wave2-verification.md).
Paired uncertainty/A-B, kNN/tabular с ансамблями/calibration, resume/диагностика,
attention, data/evaluation/product controls, ranking/forecasting intro и interview
теперь имеют материалы READY. Это не освоение учеником: TODO и ручная защита
остаются за ним; глубокие специализации PLANNED. Таблица ниже фиксирует прежние
пробелы, а не отменяет новое покрытие.

Дата: 26.09.2026. База: `03a729b`, ветка до изменений `main`, рабочая папка чистая.
В исходном каталоге 56 уроков, 88 заданий и Banking AI Lab; это материалы,
а не свидетельство прохождения учеником. Исходные проверки: 659 passed,
5 skipped, 1056 xfailed; Ruff/format и mypy (519 файлов) без ошибок.

| Компетенция | Уже есть | Пробел | Дополнение / приоритет / проверяемый результат |
| --- | --- | --- | --- |
| NumPy/vectorization | [NumPy](../modules/03_data_foundations/01_numpy/README.md), image pooling | Нет перехода к производным/autograd | Короткий [мост](../modules/04_machine_learning/07_training_bridge/README.md), CORE; update/shape tests |
| Регрессия/baseline | [Сравнение моделей](../modules/04_machine_learning/04_models/exercises/model_comparison/README.md): Dummy, Ridge, tree | Boosting отсутствует; регрессия не отсутствует | Сохраняем точный контракт; boosting — следующее углубление, не новая копия урока |
| Split/leakage/preprocessing | [Validation](../modules/04_machine_learning/02_validation/README.md), group/time split, pipelines | Нет полного модельного dataset release | Общий [протокол](experiment-protocol.md), CORE; snapshot/hash/split IDs |
| Метрики/выбор модели | [Evaluation](../modules/04_machine_learning/05_evaluation/README.md), Brier, slices, threshold, ограниченный GridSearch | Недостаточная глубина calibration/uncertainty и реальных опытов | Переиспользование сейчас; calibration/bootstrap/ablation — дальнейшее углубление |
| Артефакты | [Reproducibility](../modules/04_machine_learning/06_reproducibility/README.md), manifest exercise | Метаданные без сохранённой модели/reload | Две labs, CORE; файлы/checksums и roundtrip inference |
| Строгий зачёт | `exercise_call` превращает только NotImplementedError в xfail | `test` возвращал 0 при 13 xfail нетронутого word-index | `check ID`, CORE; fixture-regressions, ненулевой exit для incomplete/skip/zero |
| PyTorch | Нет | Нет lifecycle обучения | [Lab 01](../labs/01_pytorch_foundations/README.md), CORE; unit + CPU smoke отдельно от качества |
| Hugging Face | Нет Transformers/Datasets в исходном окружении | Нет настоящих pretrained/adaptation опытов | [Lab 02](../labs/02_huggingface_models/README.md), CORE/ML-DEPTH; offline smoke, явный live download |
| RAG/agents/production | [Модули 06–08](roadmap.md): offline doubles и локальные frameworks | Нет real embeddings/vector DB/LLM, live serving/deployment | Labs 03–06 PLANNED; не представляем фикстуры измеренным качеством |
| CI/MLOps | pytest/Ruff/mypy, Docker/Compose examples | Нет `.github/workflows` и реальной ML platform | Lifecycle/CI/tracking PLANNED, без установки MLflow сейчас |

Четыре существующих notebooks проверяются без сети с пропуском только помеченных
student code cells в копии. Это проверка примеров, не выполненных упражнений.
Новые labs используют Python-модули, не добавляют ноутбуки со скрытым состоянием.
Наличие каталога `datasets/` не означает установленную Hugging Face библиотеку:
проверять нужно distribution metadata, а не только import spec.
