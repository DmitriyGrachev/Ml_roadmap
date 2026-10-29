# Document Intelligence Lab — путь от эксперимента к системе

CORE capstone. Маленькие локальные demonstrations и самостоятельные этапы
подготовлены; весь реальный pretrained/RAG/lifecycle проект **ещё не выполнен**.
Это маршрут вашей самостоятельной работы, не готовое портфолио.
[Banking AI Lab](../banking_ai_lab/README.md) сохраняется без изменений.

## Порядок работы

| Этап | Открыть | Граница проверки |
| --- | --- | --- |
| A1: воспроизводимый baseline | [Теория, demo, отдельное задание](part_a1/README.md) | Локальный train/reload и строгий `document-a1-reproduction`; самостоятельный TODO не заполнен |
| CPU service | [API, readiness и восстановление](service/README.md) | Реальный in-process ASGI smoke; контейнер отдельно NOT_RUN |
| Вводный tracking | [Два runs и bytes](tracking_intro/README.md), [registry/restart](tracking_intro/registry-lifecycle.md) | Настоящий local MLflow author smoke выполнен; свои эксперименты и выбор модели не засчитаны |
| A: общий экзамен трём моделям | [Rules → TF-IDF → encoder](part_a/README.md) | Случайный encoder проверяет механику; pretrained качество не измерено |
| B: поиск и ответы | [Перенос Real RAG](part_b/README.md) | Полный persistent/pretrained/LLM run отделён от локального teacher |
| Эксплуатация | [vLLM](../../labs/05_model_serving/README.md), [lifecycle](../../labs/06_ml_lifecycle/README.md) | Local registry 1→2→1/restart проверен отдельно; полный lifecycle NOT_RUN; vLLM DEFERRED_ENV |
| Интеграция и защита | [Архитектура](architecture.md), [пустая структура защиты](defense-template.md) | Два разных evaluation protocol; защита REQUIRES_REVIEW |

Новичку сначала нужен [основной маршрут](../../docs/roadmap.md), а не этот capstone.
Теория Python/данных/ML не дублируется здесь. `test` проверяет инфраструктуру;
`check document-a1-reproduction` — только указанное выполненное упражнение.
Другие ручные этапы не получают автоматический зачёт от запуска teacher.

Если выбран cloud: [подготовка и необходимые решения](deployment/README.md).
Без provider/region/budget выбор не сделан, deployment не объявляется готовым.

## Исходные требования к самостоятельному проекту

Часть A: классификация публичных/синтетических документов или обращений — правила,
classical ML, pretrained encoder; prerequisites: [ML](../../modules/04_machine_learning/README.md),
[PyTorch](../../labs/01_pytorch_foundations/README.md),
[Hugging Face](../../labs/02_huggingface_models/README.md).
Часть B: RAG по разрешённой документации — prerequisites: модуль 06 и
[Real RAG](../../labs/03_real_rag/README.md). Позже bounded workflow (модуль 07)
и [serving](../../labs/05_model_serving/README.md), не произвольный автономный агент.

Expected artifacts: problem brief, data/model manifests, два evaluation протокола,
сравнение baseline, классификатор с reload, corpus/index и citations, architecture
note, error analysis, resource/cost report, ограничения, learner presentation.

Done: все решения объяснены автором, quality измерено на независимых данных;
классификация не оценивается только retrieval metric и наоборот. Проверены
no-answer, permissions, отказ внешней модели и восстановление. Выбор online/batch,
API/self-hosting, training/retrieval обоснован quality/latency/cost.
Нет реальных персональных данных, секретов в логах, исполнения модельного кода
или доверия prompt/regex как гарантии безопасности. Опасные действия требуют
подтверждения; инструменты allowlisted и выполнение ограничено.

## Независимые проекты и эксплуатационная практика

Следующий обязательный уровень — [внешнее сравнение TF-IDF / frozen / adapted](external_model_study/README.md),
[SQL data pipeline](data_pipeline/README.md) и [реальный HTTP lifecycle](production_readiness/README.md).
Прежний A1 и авторские демонстрации остаются подготовкой; новые ID требуют собственных
артефактов и [защиты](../../docs/readiness-assessment.md). Полный порядок —
[учебная карта](../../docs/learning-map.md).
