# Прикладные инструменты: углубление практики и маршрут NLP

Эта карта дополняет [общий маршрут](learning-map.md). Она отвечает на вопрос
«могу ли я самостоятельно работать с библиотекой на новой задаче», а не только
«видел ли я её API». В основе остаются Python, статистика, корректные splits,
классические baselines, ручной PyTorch loop и существующий внешний текстовый проект.

## Что добавлено в PA1

В каждом блоке есть теория с разобранным примером, маленькая авторская демонстрация,
самостоятельные TODO, поведенческие проверки, типичные ошибки и вопросы переноса.
Каталог пополнен **11 отдельными заданиями**. Проверяемые имена и порядок — в
`curriculum.toml` / `learning_tracks.toml`; `progress.md` остаётся ручным.

| Инструмент / задача | Где учиться | Что нужно сделать самому |
|---|---|---|
| NumPy | [Векторизация с масками](../modules/03_data_foundations/exercises/vectorized_features/README.md) | Стандартизация по наблюдаемым значениям, axes/broadcasting, нулевые векторы, cosine top-k с устойчивыми ties; объяснить память временных массивов |
| Pandas | [Point-in-time признаки](../modules/03_data_foundations/exercises/point_in_time_features/README.md) | Признаки в момент каждого запроса, исключение будущих и одновременных событий, сохранение identity/order, пустая история |
| scikit-learn | [Выбор pipeline и inspection](../modules/04_machine_learning/exercises/sklearn_selection/README.md) | ColumnTransformer, missing/category handling, group-disjoint CV, train-only fit, подбор C и heldout permutation importance |
| PyTorch | [Эффективность обучения](../labs/01_pytorch_foundations/exercises/training_efficiency/README.md) | Эквивалентность gradient accumulation полному batch, в том числе неравные micro-batches; отдельно реальные CUDA/AMP memory/time измерения |
| HF Datasets / Trainer / Accelerate | [Trainer workflow](../labs/02_huggingface_models/trainer_workflow/README.md) | Batched Dataset.map, dynamic collator, TrainingArguments/metrics, best validation checkpoint, сохранение и resume |
| Transformers / NER | [Token classification](../labs/02_huggingface_models/token_classification/README.md) | Subword alignment и -100, BIO entities, реальные token-classifier loss/predictions, exact span metrics, truncation и новый домен |
| TRL / PEFT | [SFT и LoRA](../labs/04_llm_finetuning/sft_workflow/README.md) | Chat template, assistant/completion loss mask, SFTTrainer, LoRA и adapter reload; base/prompt/adapter comparison на одном holdout |
| Sentence Transformers / CrossEncoder | [Нейросетевой reranker](../labs/03_real_rag/neural_reranking/README.md) | Настоящее парное scoring, candidate recall, MRR/nDCG, latency, сравнение с retrieval до reranking |
| Sentence Transformers | [Адаптация embeddings](../labs/03_real_rag/embedding_adaptation/README.md) | Query/positive/hard-negative данные, contrastive objective, query/family splits, baseline/adapted retrieval и reload |
| MLflow / Optuna | [Управление экспериментами](../projects/document_intelligence_lab/experiment_management/README.md) | Ограниченный validation-only search, trials/runs/params/artifacts, выбор модели, локальный reload и повторение predictions |
| vLLM | [Измерения и артефакты](../labs/05_model_serving/assessment/README.md) | Собственный summary сырых измерений, настоящий Linux/vLLM запуск, перезапуск, integrity/identity checks и защита |

Это продолжения существующих материалов. Например, ручной PyTorch loop нужен до
Trainer: иначе непонятно, какие обязанности библиотека взяла на себя. Аналогично
новый SFT-путь не заменяет исходное объяснение LoRA-матриц и собственный опыт PEFT.

## Маршруты и порядок

```powershell
uv run --no-sync python scripts/learn.py track ml-engineer
uv run --no-sync python scripts/learn.py track applied-ai
uv run --no-sync python scripts/learn.py track applied-nlp
```

`ml-engineer` — общая база: Python/backend/data/classic ML, внешние проекты,
PyTorch, Trainer, эффективность обучения и управление экспериментами.
`applied-ai` — широкий маршрут, включая LLM/RAG/agents и новые прикладные блоки.
`applied-nlp` — фокус на текстах, классификации, извлечении, поиске и адаптации
моделей. Он использует существующие базовые уроки, но не требует все agent-workflow
упражнения как входной билет в моделирование текстов.

Практический порядок модельной специализации:

1. Python → NumPy/Pandas/SQL → splits/metrics → sklearn baseline и внешний tabular.
2. PyTorch manual loop → resume/diagnostics → accumulation → HF model/tokenizer
   и attention → Trainer → внешний encoder study.
3. NER для нового типа выхода модели; затем LLM contracts/evaluation → SFT/LoRA.
4. Retrieval → lexical/dense/hybrid → настоящий CrossEncoder → embedding adaptation.
5. Упорядоченные MLflow/Optuna эксперименты, общий inference lifecycle, реальный
   vLLM этап по подготовке среды и итоговая защита.

MLflow нужен уже при сравнении первых моделей; порядок в формальном track фиксирует
минимальные prerequisites, а применять навыки можно во всех следующих работах.
Итоговый `check-track` запускают перед защитой, а не после каждого урока.

## Окружения без неявных загрузок

Базовый `uv sync --locked` остаётся CPU-окружением без PyTorch/HF и новых optional
ML-групп. Устанавливать `--all-groups` не нужно. Группы можно добавлять постепенно:

| Группа | Для чего | Включает |
|---|---|---|
| `training` | Исходный PyTorch/HF и accumulation | Torch, Transformers, Datasets |
| `trainer` | Trainer и NER | training + Accelerate |
| `sft` | SFT/LoRA | finetuning + TRL (Accelerate/PEFT входят в зависимость) |
| `ranking` | CrossEncoder и embedding adaptation | trainer + Sentence Transformers |
| `experiments` | MLflow/Optuna | tracking + Optuna |
| `quantization` | Только отдельный GPU/QLoRA путь | bitsandbytes; сам по себе не делает CPU torch CUDA-версией |

Пример отдельного учебного interpreter на Windows:

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".venv-training"
uv sync --locked --group migrations --group trainer --group sft --group ranking --group experiments
.venv-training/Scripts/python.exe scripts/learn.py test lab-hf-trainer-workflow
```

В PyCharm выбрать `.venv-training/Scripts/python.exe`, working directory — корень
проекта. На Linux аналогичный interpreter — `.venv-training/bin/python`.
После sync использовать этот Python либо `uv run --no-sync`, чтобы очередной
запуск не удалил дополнительные группы. CLI `check` подсказывает весь требуемый
набор, если модуль отсутствует, без импорта тяжёлых frameworks.

Установка библиотек не скачивает model weights/dataset. Каждый pretrained runner
принимает **явный локальный snapshot**. Получение разрешённых данных/модели с
фиксированной revision — отдельный осознанный шаг ученика по README блока.
Обычные тесты не получают внешние веса и не запускают server/GPU training.

## Какие методы адаптации изучать и зачем

| Метод | Что изменяется | Учебный статус |
|---|---|---|
| Frozen features + classifier | Обучается небольшая голова над готовыми представлениями | Обязательный baseline внешнего encoder study |
| Encoder fine-tuning | Веса энкодера/головы под размеченную задачу | Уже есть внешний study; Trainer и NER расширяют практику |
| SFT | Модель учится на корректных целевых ответах | Новый обязательный learner путь для NLP/Applied AI |
| LoRA | Обучаются низкоранговые adapter weights при замороженной базе | Реальная PEFT-практика и SFT-сравнение |
| QLoRA | Квантованная база + adapters, отдельные требования к вычислениям | Runnable opt-in recipe; фактический GPU опыт **NOT_RUN** |
| Embedding adaptation | Представления приближают релевантные пары и разделяют нерелевантные | Новый самостоятельный retrieval эксперимент |
| Cross-encoder reranking | Пара query/document оценивается совместно | Реальный library path; готовый pretrained reranker полезен до собственного дообучения |
| DPO / preference optimization | Используются пары предпочитаемых/отклонённых ответов | Продолжение после SFT, когда есть надёжные preference данные |
| Distillation | Студент учится воспроизводить заданное поведение teacher | Позднее под ограничения latency/cost и проверяемое качество |
| Continued pretraining | Дополнительный языковой objective на доменном тексте | Позднее, если проблема требует именно представлений/языкового распределения |

SFT — objective/данные, LoRA — способ параметризации обучения. Они совместимы и
не являются взаимоисключающими специальностями. QLoRA не заменяет dataset quality,
правильные masks и holdout. DPO/GRPO не следует добавлять ради названия: сначала
нужны определённая задача, хорошие данные и оценка, которая ловит ухудшения.

## Что достаточно считать освоением

**Механика.** Ты объясняешь shapes/masks/loss, руками выполняешь маленький пример,
решаешь learner boundary, диагностируешь неверный результат. Случайная мини-модель
подходит для проверки gradient/save/reload API, но не языкового качества.

**Библиотечный workflow.** Сам задаёшь data preprocessing, collator, configuration,
evaluation, checkpoint selection и бюджет. Сохраняешь enough artifacts, чтобы
повторить inference без скрытого состояния notebook.

**Перенос.** Берёшь новые разрешённые данные, фиксируешь train/dev/test, сравниваешь
простой baseline и адаптацию, анализируешь ошибки и ограничения. На test не
выбираешь prompt, hyperparameters или число эпох. Если адаптация хуже baseline,
это допустимый результат; нужно объяснить и воспроизвести его.

**Защита.** Другая задача/язык/label mapping не решается простой заменой строки
model id. Проверяющий просит изменить вход, объяснить предсказание и повторить
часть работы. JSON-поля, зелёный CI и authored example не доказывают авторство.

## Выбор специализации

Для текущих интересов рекомендован **Applied ML / NLP Engineer: текст, документы,
поиск и адаптация моделей**. Это рекомендация по содержанию работы. Она не обещает
самый большой рынок, короткий срок до оффера или автоматический middle-уровень
за счёт Java-стажа. [Выборка вакансий](job-market-comparison-2026-10-29.md) ограничена
и относится к своей дате; название AI Engineer само по себе не означает training.

Backend помогает в API, SQL, тестировании, диагностиках и доставке результата.
Модельную компетенцию нужно показать отдельно: данные/labels, baseline, split,
обучение, честная оценка, ошибки, воспроизводимость. NLP шире чат-ботов: классификация,
NER, matching и semantic search — полноценные задачи. Document Intelligence можно
начать с текста документов; OCR/layout/multimodal добавлять по предметной задаче.

Для портфолио достаточно двух связанных, хорошо защищённых работ после базы:

- Внешний tabular проект и затем текстовый проект с TF-IDF/frozen/adapted encoder;
  добавить NER или SFT под реальную задачу и обосновать выбор.
- Поиск на том же домене: lexical/dense/hybrid, reranking, затем адаптация embeddings,
  если хватает надёжных пар. Retrieval и ответы генератора оценивать отдельно.

Искать можно Junior ML Engineer, NLP Engineer, Applied ML/AI Engineer, AI Engineer,
Data Scientist NLP, Search/Relevance Engineer. Проверять обязанности, mentoring,
географию и уровень. Спросить команду: какие модели она обучала, кто проверяет
эксперименты и какая доля роли связана с данными/оценкой, а не только API integration.

## 8 GB VRAM и границы расширения

Главная база воспроизводится на CPU. Отдельный GPU опыт измеряет actual peak memory,
time, batch/sequence length и dtype. Репозиторий закрепляет **CPU torch**; наличие
RTX не меняет установленный runtime. Для CUDA/QLoRA/vLLM нужна явно подготовленная
совместимая среда и собственный lock/inventory. Инструкции не являются тестом
совместимости RTX 5060, драйвера и конкретного wheel.

Малый encoder и небольшой causal LM разумнее первого обязательного 7B опыта.
Ориентир 0.5–1.5B — диапазон кандидатов, не обещание вместимости: activations,
context, optimizer, kernels и KV cache также занимают память. Короткий тест
механизма и реальная модельная оценка имеют разные бюджеты.

CV, recommender systems, forecasting, DPO/GRPO и distributed training — дальнейшие
выборы, а не новый огромный обязательный курс. Текущая цель — уверенно завершать
ограниченную задачу с данными и моделями. Реальные проверки и всё оставшееся
**NOT_RUN** перечислены в [журнале PA1](applied-tools-verification.md).
