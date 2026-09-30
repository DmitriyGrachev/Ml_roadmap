# Лабораторная 02 — модели Hugging Face

Приоритет: **CORE** — загрузка, токенизация, inference, оценка и сохранение;
**ML-DEPTH** — ограниченная адаптация encoder. Материалы: **READY**.
Фактические проверки и их среда записываются в [отчёте первой волны](../../docs/wave1-verification.md).
READY не означает выполненные задания. Реальное качество MiniLM/Bitext до вашего
эксперимента — **NOT_RUN**; случайный локальный encoder этого не меняет.

Цель: сравнить три способа классификации обращений на одних данных, самостоятельно
написать обработку батчей и обучение, сохранить модель и повторить inference.
Ориентир: несколько занятий, без обязательного GPU. Не нужно проходить все восемь модулей.

## Перед началом

Нужны [Python: функции](../../modules/01_python_core/03_functions/README.md),
[классы](../../modules/01_python_core/05_data_modeling/README.md),
[I/O](../../modules/01_python_core/06_exceptions_io/README.md),
[NumPy](../../modules/03_data_foundations/01_numpy/README.md),
[validation](../../modules/04_machine_learning/02_validation/README.md),
[preprocessing](../../modules/04_machine_learning/03_preprocessing/README.md),
[оценка](../../modules/04_machine_learning/05_evaluation/README.md),
[мост к обучению](../../modules/04_machine_learning/07_training_bridge/README.md)
и [PyTorch lab](../01_pytorch_foundations/README.md).
Урок [выбора моделей](../../modules/04_machine_learning/04_models/README.md)
уже объясняет одинаковые folds и baseline — здесь применяем это к тексту.

Из корня репозитория в PowerShell или Linux:

```powershell
uv sync --group training
uv run --group training python -m labs.02_huggingface_models.example
uv run --group training python scripts/learn.py test lab-huggingface
```

Первый пример полностью локален: он создаёт маленький BERT с **случайными** весами
и словарь из Python-значений, считает logits для описаний геометрических предметов,
сохраняет safetensors и сравнивает результат после загрузки. Временные файлы удаляются.
Он учит механике API; ничего не доказывает о pretrained моделях и не пишет ваш отчёт.

PyCharm: интерпретатор `.venv\Scripts\python.exe` (Linux `.venv/bin/python`),
working directory — корень репозитория; запуск по имени модуля, а не по пути `example.py`.
Подробности ресурсов: [compute guide](../../docs/compute-guide.md).

## Что происходит внутри encoder

Tokenizer превращает текст в ID фрагментов слов, добавляет специальные токены и
сохраняет их порядок. Это часть модели: другой словарь меняет смысл тех же ID.
`padding` выравнивает длины в батче; `truncation` ограничивает длину, теряя часть текста.
`attention_mask=1` означает настоящий токен, `0` — padding. Сам ID padding не заменяет
маску. `token_type_ids` различает сегменты в BERT; у других архитектур этого поля может
не быть. Контракт этой лабораторной намеренно привязан к BERT/MiniLM.

Self-attention смешивает представления токенов с учётом контекста; позиционные embeddings
передают порядок. Encoder использует контекст с обеих сторон и удобен для представления
текста/классификации. Causal decoder обучается предсказывать следующий токен с маской
будущего. Четыре logits classifier — оценки классов, а не четыре следующих слова и
не вероятности. `CrossEntropyLoss` принимает logits и целочисленные метки; `softmax`
перед loss здесь не нужен. На inference вероятности можно получить отдельно.
Пошаговый shape trace, сравнение архитектур и отдельное CPU-упражнение с масками:
[Механика attention](attention_mechanics/README.md).

Для frozen MiniLM нужны embeddings предложений: выход последнего слоя имеет форму
`[batch, tokens, hidden]`. Усредняйте только позиции с mask=1, затем нормализуйте
вектор по L2. Среднее вместе с padding меняется при добавлении более длинного соседа
в батч — это ошибка. Нулевой вектор после нормализации остаётся нулевым.
`model.eval()` управляет dropout; `torch.inference_mode()` отключает граф производных.
Эти вызовы решают разные задачи.

## Ресурсы и явная загрузка

Проверено по карточкам и метаданным Hub 26.09.2026. Полная машиночитаемая фиксация
файлов, размеров и SHA-256: [resources.json](resources.json).

| Ресурс | Фиксация и назначение |
| --- | --- |
| `sentence-transformers/all-MiniLM-L6-v2` | Revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, Apache-2.0; английский encoder, 384-мерные sentence embeddings. Safetensors: 90 868 376 байт. |
| `bitext/Bitext-customer-support-llm-chatbot-training-dataset` | Revision `430d1a89bd93bd1fa23c16f29dd53e73f0087443`, CDLA-Sharing-1.0; hybrid synthetic данные. CSV v11: 19 202 474 байта. |

Карточки: [модель](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41),
[датасет](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset/tree/430d1a89bd93bd1fa23c16f29dd53e73f0087443).
Изучите условия лицензий до распространения производных данных/артефактов;
лицензия репозитория курса не заменяет лицензии ресурсов. Сохраняйте attribution
Bitext Innovations и сведения о преобразованиях с dataset snapshot.

Нужен только столбец `instruction` как X, а `intent` как y. Выбираем `ACCOUNT`:
`create_account`, `delete_account`, `edit_account`, `switch_account` (ID 0–3 именно
в этом порядке). `response`, `intent`, `category`, `flags` **не входят в признаки**;
ответ содержит подсказку к метке, category/flags служат только аудиту.
Другие intent исключаются. Данные английские: это не проверка русского языка.

Команда ниже — отдельное осознанное сетевое действие. Она скачивает семь конкретных
файлов, примерно **110.8 MB** суммарно; не весь model repository, не PyTorch `.bin`,
не ONNX/OpenVINO и не дополнительную копию весов. Ключи и платные API не нужны.
Каждый файл проверяется по размеру и SHA-256; повторный запуск использует проверенный
кэш. При несовпадении или `.partial` команда останавливается: сначала осмотрите
путь и удалите только неудачный файл, затем повторите команду.

```powershell
uv run --group training python -m labs.02_huggingface_models.download
```

По умолчанию кэш — `.cache/roadmap-huggingface/`. Не коммитьте кэш, веса и результаты.
Ни import, ни pytest, ни `uv sync` эти данные/веса не загружают.
`run real` использует только этот проверенный кэш: читает небольшой CSV через
`csv.DictReader` и создаёт `Datasets.Dataset.from_list` в памяти. Это также избегает
длинных имён cache-lock файлов Datasets на Windows.

Оценки ресурсов, **не измерения**: local smoke — CPU и менее 1 GB добавочной RAM;
реальный малый запуск — 2–4 GB RAM и 0.5–1 GB свободного диска поверх окружения.
CPU достаточен. VRAM не требуется; совместимость CUDA на вашем GPU здесь не проверена.
Начальный бюджет, также не измеренный: 64/16/16 строк на класс train/validation/test,
batch=4, max_length=64, max_steps=20, seed=17, learning_rate=2e-5. Это ограниченный
учебный прогон, не репрезентативный benchmark и не обещание полезной accuracy.

## Четыре содержательных задания

Меняйте [starter.py](starter.py); сохраняйте тесты. Вспомогательные функции можно
добавлять рядом. Готовых реализаций и скрытых решений нет.

### 1. Подготовьте snapshot и split

`prepare_splits(rows, seed, counts)`:

- Проверьте неотрицательный целочисленный seed и три положительных целочисленных
  counts (bool не считается int). Требуемые поля — instruction/intent/category.
  Для выбранных intent category обязана быть ACCOUNT, instruction — непустая строка.
- Нормализуйте X: Unicode NFKC → casefold → пробелы через `" ".join(text.split())`.
  Эта политика одинакова при обучении и inference; сохраните её имя `nfkc-casefold-space-v1`.
- До split удалите одинаковые нормализованные тексты. Разные метки у одного текста
  означают `ValueError` с `conflict`: их нельзя молча разрешить первой строкой.
  ID — SHA-256 UTF-8 нормализованного текста. В `Document.text` храните этот текст.
- Для каждой метки отсортируйте по ID, перемешайте локальным `random.Random(seed)`
  в порядке LABELS и возьмите counts строк на train/validation/test последовательно.
  Нехватка строк — ValueError, не уменьшение test без уведомления. Внутри каждого
  итогового split сортируйте по ID. Перестановка входных строк не меняет результат.
- Верните ровно train/validation/test → списки `Document`; исходные строки не меняйте.

Результат: сохранённые нормализованные строки, исходный pinned CSV, хэши, split IDs
и объяснение дедупликации. Точные дубликаты устранены, но семантически похожие
синтетические шаблоны всё ещё могут попасть в разные splits. `flags` не являются
надёжным ID исходного шаблона. Проверьте вручную похожие формулировки; перечислите
ограничение в анализе. Не называйте такой test оценкой реального потока клиентов.

Мини-инструкция разметки: create — новое членство; delete — закрытие; edit — изменение
текущего профиля; switch — переход на другой существующий профиль. «Change my account»
неоднозначно: зафиксируйте конфликт и необходимость уточнения. В отдельной заметке
проверьте не менее двух таких пограничных примеров и одну ошибочную метку.

### 2. Кодируйте батчи и извлекайте embeddings

`encode_batch` принимает непустую последовательность непустых строк и max_length>=2.
Возвращает CPU `torch.long` tensors `input_ids`, `attention_mask`, `token_type_ids`,
сохраняя порядок. `padding=True`, `truncation=True`, `return_tensors="pt"`;
padding только справа. Не дополняйте каждый батч до глобального лимита без причины.

`masked_mean_pool` принимает конечный floating tensor `[B,T,H]` и бинарную маску
`[B,T]` на том же device. Несовпадение размеров, нечисловые маски и строки без
настоящих токенов — ValueError с `mask`; NaN/inf — с `finite`. Возвращает `[B,H]`,
сохраняя dtype/device, сначала среднее без padding, потом L2-нормализация.
Не меняйте аргументы. Сохраняйте возможность вычисления градиента.

Результат: одинаковое представление текста при изменении длины его соседей в батче
в eval mode (с допустимой численной погрешностью), включая последний неполный батч.

### 3. Ограниченно адаптируйте encoder и сохраните модель

`adapt_encoder` принимает BERT classifier с четырьмя logits, непустые train/validation
и `RunConfig`. Зафиксируйте seed локального генератора DataLoader, перемешивайте только
train. Не меняйте записи и не используйте test. Заморозьте всё, затем включите градиенты
только для `model.bert.encoder.layer[-1]` и `model.classifier`. Pooler и ранние слои
остаются замороженными. Это обычная частичная адаптация encoder, **не LoRA**.

Обучите ровно max_steps обновлений AdamW, повторяя проходы при необходимости,
learning_rate из config, weight_decay=0.0. На каждом шаге сбрасывайте градиенты,
считайте cross-entropy по logits, проверяйте конечность loss, делайте backward/step.
История содержит loss каждого шага. В конце eval/inference_mode: средняя loss по
**всем примерам** validation с учётом размера последнего батча. Верните `TrainingHistory`;
оставьте модель в eval. Некорректные параметры, метки, пустые данные — ValueError.
NaN loss — явная ошибка, не пропуск батча. Используйте device параметров модели.

Проверьте, что последние веса действительно изменились, а первые — нет. Если модель
не может выучить очень маленькую подвыборку, сначала проверьте labels, masks,
requires_grad, zero_grad, LR и train/eval, затем увеличивайте данные.

`save_and_reload` сохраняет модель с safe_serialization=True и tokenizer в пустую
директорию; непустую директорию не перезаписывает. Загружает через AutoModelForSequenceClassification
и AutoTokenizer **только локально**, `trust_remote_code=False`, `use_safetensors=True`
для модели. Возвращает пару в eval mode на CPU. Сохраняйте label mapping в config.
После reload logits фиксированного батча должны совпасть с исходными eval logits
в пределах погрешности. Путь к неизвестному pickle/joblib не загружайте.

Сравните с `Trainer`: он организует batches, optimizer steps, evaluation и checkpointing,
но не выбирает честный split и метрику за вас. Здесь ручной loop показывает эти границы.
Переход на Trainer — последующий эксперимент; сам transformer с нуля реализовывать не нужно.

### 4. Сравните три метода и объясните результат

`compare_models` получает локальную модель, одни и те же splits, config и директорию
checkpoint. Сначала реализуйте offline exercise на [local_fixture.py](local_fixture.py)
через `run_offline_experiment`; это отдельный маленький случайный encoder.
Затем после явной загрузки используйте реальные ресурсы:

1. `TfidfVectorizer` + `LogisticRegression(max_iter=300, random_state=seed)`; словарь/IDF
   учатся только на train. Остальные настройки оставьте default и запишите их.
2. Frozen `AutoModel` MiniLM + ваше masked pooling/L2 + такой же LogisticRegression.
   Encoder всегда eval/inference_mode, извлечение батчами. Используйте вашу функцию
   `masked_mean_pool`. Классификатор fit только train; оба линейных метода вызывают
   `predict` на признаках test и записывают именно эти результаты.
3. `AutoModelForSequenceClassification` из того же MiniLM с новой головой num_labels=4,
   явными id2label/label2id; seed перед созданием головы. Затем ваш `adapt_encoder`
   и `save_and_reload`. Используйте именно ваши учебные функции, чтобы их контракты
   сохранялись при сравнении. Используйте одинаковый tokenizer/max_length для методов 2–3.

При каждой загрузке: путь из cache, local_files_only=True, trust_remote_code=False;
для модели use_safetensors=True. Предупреждение о новой classifier head ожидаемо:
MiniLM обучался на предложениях и не имеет готовой головы для этих четырёх intent.
Не разрешайте случайно переинициализировать весь encoder из config вместо загрузки весов.

Выбор бюджета, настроек или threshold делается на validation; test используйте после
заморозки решения. Здесь argmax, отдельный threshold не нужен. На test верните для
каждого метода `predictions` в порядке test IDs, `accuracy`, `macro_f1` (все четыре
label, zero_division=0), `warm_seconds` и `peak_memory_bytes`/`memory_note`.
Измеряйте время через perf_counter: один warm-up, затем три прохода по одному test
на CPU, среднее полное время одного прохода. Включайте preprocessing и model inference.
Запишите входные длины, batch, device и то, что загрузка/обучение не входит в latency.
Память — измеренный peak RSS внешним монитором процесса с описанием метода, либо null
и `NOT_MEASURED: причина`; tracemalloc не измеряет всю нативную память PyTorch.

Сохраните adapted checkpoint. Сравните confusion matrix, ошибки минимум по двум
сегментам (например, короткие/длинные запросы и flags для аудита), неоднозначные примеры,
время и память. Один заранее выбранный ablation — CLS вместо masked mean pooling
на validation; после анализа не подглядывайте в test для выбора pooling.
Никакой метод не обязан выиграть. Одинаковые числа между CPU/GPU не обещаются.

## Подсказки по уровням

1. Сначала выпишите формы и инварианты: какие строки разрешены, что означает каждая
   ось, какие параметры могут изменяться, какие артефакты нужны после завершения процесса.
2. Для dedup нужен ключ по нормализованному содержимому, а не исходному индексу CSV.
   Для pooling расширьте mask на последнюю ось. Для адаптации распечатайте имена
   trainable параметров до optimizer; validation loss агрегируйте по числу строк.
3. Если результат зависит от соседей в батче — проверьте padding/mask и eval.
   Если веса стоят — requires_grad и optimizer должны ссылаться на те же параметры.
   Если reload меняет logits — сравните tokenizer/config, режим eval и dtype.
   Если сильная модель хуже — сначала проверьте протокол, затем допустите отрицательный результат.

## Артефакты и строгий зачёт

Офлайн-зачёт и внешний эксперимент различаются. После самостоятельной реализации:

```powershell
uv run --group training python -m labs.02_huggingface_models.run offline
uv run --group training python -m labs.02_huggingface_models.run validate-offline
uv run --group training python scripts/learn.py check lab-huggingface
```

Обязательная папка `generated-reports/huggingface/`: `offline-report.json`, `data.json`,
`splits.json`, `analysis.md`, `checkpoint/` с safetensors, config и tokenizer.
`run_offline_experiment` — ваш TODO: он не создаёт фиктивный отчёт до реализации.
Запустите локальные 16 строк с counts=(2,1,1), маленьким random encoder, адаптацией,
reload и вычисленными predictions. Можно расширить локальный словарь для этих слов;
зафиксируйте точную версию словаря с checkpoint и проверьте долю UNK.

Схема `offline-report.json` (значения вычисляете вы, файл-шаблон намеренно не заполнен):

- schema_version=1; evidence=`LOCAL_RANDOM_ENCODER_STUDENT_RUN`;
  pretrained_quality=`NOT_RUN`; seed; model={`id`: `local-random-bert`, `revision`: `fixture-v1`}.
- config: batch_size, max_length, max_steps, конечный положительный learning_rate
  и preprocessing=`nfkc-casefold-space-v1`;
  versions: python, torch, transformers, datasets, scikit_learn; code_revision.
- data и splits: объект с относительным path и SHA-256 фактических байтов файла.
  `data.json`: объект records со всеми `{row_id, text, label}`; `splits.json`:
  train/validation/test → массивы ID. Сохранённые строки полностью покрывают splits.
- checkpoint_files: относительный путь каждого файла checkpoint → SHA-256. Обязательно
  checkpoint/model.safetensors, checkpoint/config.json, checkpoint/tokenizer.json.
- test_ids, labels, predictions в одном порядке; вычисленные accuracy и macro_f1.
  Метрики пересчитываются; проверка снова загружает checkpoint локально и сверяет predictions.

`analysis.md` — ваш текст от 200 символов, без TODO/заглушек: постановка, baseline,
протокол, наблюдения по ошибкам, ограничения, затраты и следующий эксперимент.
Добавьте короткую защиту на английском: what you built, how you measured it, limitations.
Автоматическая проверка наличия/структуры текста не оценивает качество рассуждений;
это отдельная ручная проверка. Метрики не доказывают, что вы поняли эксперимент.

Для реальной модели отдельная команда после выполнения compare_models:

```powershell
uv run --group training python -m labs.02_huggingface_models.run real --output generated-reports/huggingface-real
```

Она сохраняет `selected-data.json`, `splits.json`, `report.json` с исходными revisions,
config, версиями, измеренными результатами трёх методов и checkpoint. Добавьте собственный
`analysis.md`; команда уже фиксирует code revision, dirty status, preprocessing policy
и checksum каждого checkpoint-файла. При dirty status сохраните собственный patch
вместе с результатом: commit SHA сам по себе не включает незакоммиченные изменения.
До сохранения report команда заново загружает adapted checkpoint и проверяет,
что его test predictions совпадают с результатами сравнения.
Повторный запуск требует новой пустой директории, чтобы не потерять прошлый эксперимент.
Предыдущий pinned CSV сохраняется в cache: одного названия датасета для воспроизведения мало.
Реальный эксперимент не выполняется стандартным pytest и не является обязательным
GPU-зачётом. LIVE_VERIFIED записывайте только после его фактической проверки с командой,
средой, моделью, данными и границами результата.

Focused tests: `uv run --group training pytest labs/02_huggingface_models -q -rx`.
Неизменённые student boundaries дают xfail health и ненулевой strict check.
Отсутствие training group — NOT_RUN/skip health, а не PASS лабораторной.
Не меняйте тесты и не копируйте временные test fixtures в ученический отчёт.

## Вопросы для защиты

1. Почему один tokenizer и max_length нужны и при training, и после reload?
2. Что теряется при truncation и как измерить частоту усечений на выбранном split?
3. Почему last hidden state сам по себе не является sentence embedding?
4. Что произойдёт, если перед CrossEntropyLoss применить softmax?
5. Почему удаление точных дубликатов не устраняет template leakage?
6. Как доказать, что frozen encoder действительно не обновился, а новая голова обучается?
7. Как отличить плохой эксперимент от честного результата «TF-IDF лучше»?
8. Какие сохранённые bytes нужны другому человеку, чтобы повторить ваши predictions?

Готово, когда строгий offline check проходит, вы объясняете контракты и сохранённые
предсказания воспроизводятся. Для реальной части отдельно требуются сравнение и анализ;
в трекере отмечайте только ту работу, которую действительно сделали сами.

Официальные справочники: [BERT API](https://huggingface.co/docs/transformers/v5.17.0/en/model_doc/bert),
[padding/truncation](https://huggingface.co/docs/transformers/v5.17.0/en/pad_truncation),
[save/load](https://huggingface.co/docs/transformers/v5.17.0/en/main_classes/model),
[Datasets: локальные файлы](https://huggingface.co/docs/datasets/loading),
[training](https://huggingface.co/docs/transformers/v5.17.0/en/training).
