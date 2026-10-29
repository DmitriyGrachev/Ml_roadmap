# Независимый проект: TF-IDF, frozen и adapted pretrained encoder

ID: **`document-external-model-study`**. Обязательный эксперимент с настоящими
внешними данными и pretrained весами. До собственного запуска качество — **NOT_RUN**.
Авторская демонстрация, offline random BERT и успешный импорт Transformers не являются
выполнением этого проекта. Ориентир — 4–6 занятий, CPU достаточно для малого бюджета.

Prerequisites: [lab 02](../../../labs/02_huggingface_models/README.md),
[Document Intelligence A1](../part_a1/README.md),
[tabular study](../../external_tabular/README.md), теория train/dev/test, TF-IDF,
linear classifier, attention mask, masked mean pooling/L2, cross-entropy и backprop.
Прочитайте [контракты проекта](../contracts.py) и [архитектуру](../architecture.md).
Команды — из корня, PyCharm запускает модули с `.venv` и working directory корня.

## Постановка и выбор источника

Классифицируем английское обращение по четырём ACCOUNT intent: create, delete,
edit, switch; порядок ID **0,1,2,3** задан `labs/02_huggingface_models/starter.py`.
Вход сервиса — только `instruction`, до маршрутизации обращения. `intent` — target,
`response` содержит подсказки к нему и запрещён в X; `category` и `flags` допускаются
только как audit metadata. Измеряем одинаковую задачу, а не три разных набора строк.

Основной low-compute маршрут повторно использует уже закреплённые ресурсы lab 02:

| Ресурс | Назначение и источник | Фиксация |
| --- | --- | --- |
| Bitext customer support | [Карточка источника](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset), hybrid synthetic English data | Dataset revision, точный CSV, размер и SHA-256 из [resources.json](../../../labs/02_huggingface_models/resources.json); CDLA-Sharing-1.0 |
| all-MiniLM-L6-v2 | [Официальная карточка модели](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), 384-d sentence embeddings | Pinned revision и шесть разрешённых файлов из того же manifest; Apache-2.0 |

Карточки просмотрены 28.10.2026 UTC; для воспроизводимости используйте именно revisions
в manifest, а не изменяемый `main`. Лицензия encoder и лицензия текста различаются:
запишите attribution Bitext Innovations, условия распространения производных данных,
модель, revisions, URL, дату получения и все преобразования. Не переносите лицензию
кода курса на эти данные. Собственные внутренние документы нельзя отправлять на Hub/API.
Альтернативы — AG News, другой язык, собственная разрешённая коллекция документов —
годятся для transfer, но требуют нового source adapter/license/split contract.
Не подменяйте ими pinned данные в JSON, сохраняя чужие hashes.

Сначала локальная механика, затем отдельное осознанное скачивание:

```powershell
uv sync --group training
uv run python -m projects.document_intelligence_lab.external_model_study.demo --output generated-reports/external-text-author
uv run --group training python -m labs.02_huggingface_models.download
```

Последняя команда явно загружает только файлы закреплённого manifest (~111 MB),
проверяет размер/хэш и использует `.cache/roadmap-huggingface/`. Ни один обычный тест
этого проекта не инициирует download. `verify_cache` и все model loaders работают
локально с `trust_remote_code=False`, `use_safetensors=True`; pickle здесь не нужен.

## Самостоятельные решения до final holdout

Создайте собственный `analysis.md`, в котором есть задача, допустимые input features,
критерий успеха, неоднозначные метки, ограничения английского synthetic источника
и протокол сравнения. Примеры «change my account» и «switch email» могут требовать
уточнения; проверьте хотя бы две неоднозначные и одну подозрительную метку вручную.

Используйте свои реализации lab 02 `prepare_splits`, `encode_batch`,
`masked_mean_pool`, `adapt_encoder`, `save_and_reload`, `compare_models`.
Новые выполненные решения этих границ проект не предоставляет.
`prepare_splits` делает NFKC/casefold/whitespace normalization, content SHA IDs,
удаляет normalized exact duplicates и отклоняет конфликтующие метки.
Это не устраняет близкие paraphrase/template families.

До отбора моделей аудируйте соседние формулировки; создайте `groups` — словарь
row_id → независимо проверенная template/collection family. Одинаковая family
не может пересекать splits. Один row ID на группу допустим только после объяснения,
что точные дубликаты удалены, а надёжного family ID у источника нет; так нельзя
заявлять отсутствие semantic leakage. `flags` не являются надёжным template ID.
Для строгого group holdout переопределите split на уровне family и запустите те же
интерфейсы `compare_models` на новом split. Сохраняйте причины исключений/группировки.

Зафиксируйте ordered `train/validation/test` manifests и их SHA **до** сравнения.
Начальный CPU бюджет lab: 64/16/16 строк **на класс**, batch=4, max_length=64,
max_steps=20, LR=2e-5; это пример маленького эксперимента, не benchmark.
Сначала проверьте пайплайн на 16/4/8 на класс; после диагностики выбирайте бюджет
на validation. Обоснуйте representativeness и широкую неопределённость малой выборки.
Если все данные от одного synthetic генератора, такой test не доказывает перенос
на реальные обращения. Не выдумывайте временной порядок, которого нет в source.

## Три метода, один split и честный бюджет

1. **TF-IDF + LogisticRegression**: словарь/IDF fit только train;
   `TfidfVectorizer()` и `LogisticRegression(max_iter=300, random_state=seed)`,
   остальные параметры default. Внешний технический replay привязан к этому baseline.
2. **Frozen pretrained MiniLM + linear**: `AutoModel.from_pretrained(local_model_dir, ...)`,
   eval/inference_mode, ваше masked mean pooling **без padding**, L2 normalization,
   тот же tokenizer/max_length, train-only такой же LogisticRegression.
   Все encoder weights должны оставаться равны pinned base weights.
3. **Adapted encoder**: из того же реального pretrained MiniLM создайте
   `AutoModelForSequenceClassification(num_labels=4)` с новой головой. Seed до
   инициализации головы. Trainable только последний BERT block и classifier;
   pooler/ранние blocks заморожены. Сохраните loss каждого optimizer step,
   измеренную среднюю validation loss по всем строкам, checkpoint и tokenizer.

Одинаковая segmentation/max_length нужна для содержательного сравнения 2–3.
Случайные веса `BertConfig(...)` допустимы для shape/gradient smoke, но не содержат
полученного на внешнем корпусе представления. Их нельзя сделать pretrained моделью
переименованием `id`. Gate проверяет **закреплённые байты base** и сравнивает
состояния encoder: ранние веса неизменны, последний block действительно изменился.
Проверка новой головы сама по себе была бы недостаточна: это мог быть ещё один frozen run.

Заранее выберите ограниченный поиск для адаптации на validation, например 10/20/40 steps
при одном LR, потом один контроль LR; запишите все попытки и бюджет. Выберите
правило при ничьей (простота/latency), перед финалом заморозьте решение.
Ни один метод не обязан выиграть. TF-IDF может быть сильнее на коротких шаблонах;
малое число шагов адаптации может ухудшить перенос. Это корректный результат,
если протокол и evidence воспроизводимы. CLS vs masked mean изучите как отдельный
ablation **на validation**, не как повод подбирать pooling по test.

Ниже оценки для планирования, не наши измерения: несколько GB RAM и 0.5–1 GB диска
поверх окружения на CPU. Batch=2 при нехватке RAM; max_length=32 допустим после
измерения truncation на train/dev. Сохраните реальный wall time, batch, длины,
систему/CPU, versions, peak RSS либо `NOT_MEASURED` с причиной. При медленном CPU
ограничьте количество потоков PyTorch в своём runner и запишите его. Не обещайте
пользователю скорость по этим оценкам. GPU — добровольное ускорение: отдельно
проверьте CUDA PyTorch environment, перенесите model/batches на device, сохраните
конфиг; публичный replay использует CPU, численная погрешность может изменить argmax.
Если CPU/GPU predictions расходятся, объясните boundary cases и сохраните обе версии.

## Измерение, uncertainty и перенос

На том же locked test сохраните все labels и predictions, confusion matrix,
accuracy и macro-F1 по всем четырём labels. Latency — после warm-up, preprocessing
и inference включены, загрузка и fit исключены; lab предусматривает три warm прохода.
Не сравнивайте warm TF-IDF с cold transformer, не называйте `tracemalloc` полным RSS.

Сравнение `adapted_encoder − tfidf_linear` в этом проекте использует парный bootstrap
macro-F1: 1000 одинаковых resampled test index arrays для обоих методов, seed=17,
95% percentile interval. `make_evaluation` пересчитывает его из saved predictions.
Это **условная** неопределённость при фиксированном обучении и IID строках.
Для template families нужен group/cluster bootstrap как отдельное расширение.
Никакой интервал по фиксированным predictions не заменяет полное переобучение:
повторите весь fitting с несколькими seeds на locked validation и сравните
initialization, train sampling, вариацию head и last block. Для полной оценки split
sensitivity используйте отдельный dev-only протокол; final test не превращайте в dev.
Сохраните measured runs и число повторов; отсутствие большой GPU серии не оправдывает
выдуманные результаты. Обязательное упражнение по повторному training в основном
маршруте проверяет такие артефакты отдельно.

Нужны минимум два проверяемых error slices: true intent, короткие/длинные запросы,
ошибки с placeholder/entity, неоднозначные create/edit и delete/switch; train-derived
границы длин фиксируются до test. Срезы сохраняют конкретные test IDs и metrics
каждого метода. `make_evaluation` автоматически создаёт true-label slices как минимум
арифметики; собственная аналитика должна выходить за их перечисление.
Разберите не менее 5 ошибок или все, если их меньше: текст, truth, predictions трёх
методов, family, вероятная причина, корректная граница inference и следующий опыт.
Для всех трёх правильных ответов на маленьком test не фабрикуйте ошибки — обсудите
ограниченную мощность проверки и добавьте новый независимо размеченный dev challenge.

## Запуск и упаковка собственных результатов

Реализуйте [starter.py](starter.py) `run_study(cache, output, seed=23)` и оставшиеся
границы lab 02. Runner может использовать lab `run_real` после самостоятельного
аудита splits либо вызывать тот же `compare_models` с family-aware split.
Реализацию runner и независимый повторный запуск проверяют на человеческой защите.
Допустим другой самостоятельно написанный entry point с тем же воспроизводимым
протоколом; сохраните его исходники и точную команду. Технический PASS проверяет
реальные сохранённые артефакты и model replay, не вызывает `run_study` и не требует
именно эту обёртку. Default offline tests не повторяют pretrained training.
Сохраните training history до выхода из процесса: существующий lab report содержит
predictions/configs, но не полную историю optimizer loss.

```powershell
uv run --group training python -m labs.02_huggingface_models.run real --output generated-reports/my-text-real
```

В чистой папке своего исследования самостоятельно напишите `study.json` и
`analysis.md` и сохраните исходник runner. Готовых ответов/значений в репозитории нет.
Поле `groups` должно покрывать ровно все selected row IDs; если audited groups
пересекают splits, сначала пересоздайте split/experiment, не меняйте family labels
ради прохождения gate. Затем упаковка:

```powershell
uv run --group training python -m projects.document_intelligence_lab.external_model_study.assemble --real-run generated-reports/my-text-real --study generated-reports/my-study/study.json --analysis generated-reports/my-study/analysis.md --code generated-reports/my-study/experiment.py --output projects/document_intelligence_lab/external_model_study/submission
uv run --group training python -m projects.document_intelligence_lab.external_model_study.protocol projects/document_intelligence_lab/external_model_study/submission
uv run --group training python scripts/learn.py check document-external-model-study
```

[assemble.py](assemble.py) — упаковщик, не выполненное исследование. Он принимает
только `PRETRAINED_MODEL_STUDENT_RUN`, проверяет local cache, копирует raw CSV,
selected data/split, реальный base и adapted checkpoint, исходник learner lab boundaries,
versions, config и ваш analysis; считает hashes, evaluation, conditional bootstrap
и запускает replay. Папка output должна быть пустой. `submission/` игнорируется Git;
не добавляйте CSV, weights, generated reports или learner completion ticks в commit.
Скопированная base нужна для автономной проверки, поэтому output занимает ещё ~200 MB.
Можно хранить рядом несколько запусков, не перезаписывая один другим.

Схема вашего `study.json` до упаковки:

| Поле | Что вы сохраняете |
| --- | --- |
| `groups` | Все selected row IDs → audit family ID |
| `retrieved_at`, `permission_note` | Дата исходного получения, attribution, лицензия/разрешения, преобразования |
| `feature_availability` | Что разрешено использовать при inference и почему response/category/intent исключены |
| `leakage_audit`, `split_rationale` | Dedup/conflicts, semantic/template leakage, split rationale и counts |
| `selection_rule`, `selection` | Правило до test; `selection.used_split="validation"`, выбранный метод/конфиг и dev score |
| `training_history` | `train_losses` длины max_steps, `validation_loss`, `validation_count` |
| `error_analysis`, `limitations`, `transfer_question` | Собственные выводы с ID, ограничения популяции/compute, незнакомое изменение |

Упаковщик добавляет **из реального lab report**, а не по вашему текстовому утверждению:
`model`, `dataset`, `config`, `preprocessing`, `versions`, `code_revision`, `code_dirty`.
`config` включает seed, batch_size, max_length, max_steps, learning_rate.
При dirty state сохраните patch/дополнительные исходники в artifacts — Git SHA не
содержит незакоммиченные изменения. Можно добавить дополнительные slices и hashes
своим writer, сохраняя [общий bundle contract](../../external_tabular/evidence.py).
Manifest schema/project/evidence_kind и `raw/data/splits/evaluation/source/code/analysis/study`
обязательны, каждый artifact имеет относительный path и SHA-256.

## Что проверяется автоматически и что защищаете вы

`validate_submission` требует правильные source/weight bytes по pinned manifest,
проверяет происхождение каждой выбранной normalized строки и label из CSV,
применяет **существующие Document Intelligence** dataset/split/group contracts,
пересчитывает metrics, uncertainty и slices. Затем fit повторяется для TF-IDF и
frozen linear head на train, извлекаются pretrained embeddings через ваши lab-функции,
а adapted predictions заново вычисляются из сохранённого safetensors checkpoint.
Проверка ранних/последних encoder weights отсекает random-only и head-only подмену.
Неизвестные checkpoint files/симлинки не подгружаются мимо manifest.
Base tokenizer остаётся закреплён по исходным bytes. Для adapted tokenizer gate
сравнивает загруженные vocabulary/added tokens, normalizer, pre/post-processing,
special tokens и значимые настройки из вспомогательных JSON, включая
padding/truncation side. Обычная токенизация с padding/truncation может изменить
сохранённый backend cache; это допустимо, поскольку evaluation явно задаёт
`padding=True`, `truncation=True`, `max_length`. Совпадение целого tokenizer.json
байт-в-байт после encode/save не требуется; hashes каждого сохранённого artifact
по-прежнему проверяются. Изменение значимой токенизации или направления padding
не допускается даже при неизменённом tokenizer.json.

Технический `VERIFIED` означает согласованность этих evidence, а не доказанное
авторство, независимость template families, качество русского языка или production
readiness. Хэши/копия source code не доказывают, что это код данного запуска, а loss
list не доказывает каждое optimizer update. Ревьюер просит воспроизвести свой runner,
показать логи/выбор на dev и объяснить конкретные ошибки. Текстовые поля проверяются
на наличие; их смысл, независимость работы и честность timeline — ручная оценка.
`human_review="REQUIRED"` не превращается в PASS от любой непустой строки отчёта.

Offline maintainer tests:

```powershell
uv run pytest projects/external_tabular projects/document_intelligence_lab/external_model_study -q -rx
```

Они не загружают модель и не измеряют её качество. Отсутствие learner manifest даёт
один xfail в `test_submission.py`; strict check считает это незавершённой обязательной
работой. Другой ID `lab-huggingface` сохраняет собственный offline scope.
Нельзя отмечать новый внешний проект по старому random-encoder report.

| Область | Слабое evidence | Сильное evidence |
| --- | --- | --- |
| Источник | Название Hub repo | Revision, bytes/hashes, разрешения, raw→selected derivation и audit |
| Pretrained | «Использовал BERT» | Pinned weights, padding-safe pooling, frozen/adapted state comparison и reload |
| Сравнение | Три числа на разных наборах | Одинаковые ID/labels, train-only fitting, dev selection, сохранённые paired predictions |
| Интерпретация | «Transformer обязан быть лучше» | Объяснение честного проигрыша, uncertainty, затраты и ошибки по slices |
| Авторство | Непустой analysis | Живое воспроизведение, объяснение масок/параметров и независимый transfer |

На защите покажите shapes одного последнего неполного батча, объясните
`eval` vs `inference_mode`, причину новой classifier head и trainable parameter names.
Ревьюер меняет одну строку, padding соседа или max_length и просит предсказать,
какие outputs/инварианты должны измениться.
**Transfer task:** новый intent либо русский/реальный разрешённый набор с новым
locked holdout. Сначала измерьте fixed model без адаптации, затем перепроектируйте
label mapping/tokenizer/model choice и split. Английская MiniLM не доказывает русский
перенос. Отдельно сравните family-held-out и случайный split без переиспользования final test.

## Необязательное расширение: base / prompt / LoRA

Это расширение, не условие CPU-зачёта. Для небольшого разрешённого causal LM выберите
revision/license и заранее бюджет. Сравните base, один dev-selected prompt с явным
label verbalizer и LoRA adapter на **том же locked holdout**; одинаковые tokenizer,
max_new_tokens, decoding, parser и обработка abstain/invalid outputs. Сохраните raw
outputs и parser errors, macro-F1/coverage, latency/RSS, trainable parameter counts,
adapter/base hashes и compute. Prompt примеры не должны брать финальные строки.
Проверьте leakage pretrained training corpus насколько это возможно; отсутствие
доступа к нему честно укажите. Negative result LoRA допустим; без реального запуска
пишите `NOT_RUN`. PEFT меняет часть весов/добавляет low-rank параметры; это не тот
же эксперимент, что last-block adaptation выше. GPU может помочь, но обязательной
платной модели/API и требования GPU нет. Материалы — существующий finetuning group
и [compute guide](../../../docs/compute-guide.md).

После защиты подключите выбранный checkpoint к [Document Intelligence service](../service/README.md):
сохраните один preprocessing contract для train/serve, прогоните независимые API
запросы и отдельно измерьте latency/failure/restart. Модельное качество и HTTP
надёжность — разные доказательства; хороший F1 не заменяет проверку сервиса.

### Отдельный авторский smoke на уже скачанных реальных ресурсах

После явной команды `labs.02_huggingface_models.download` можно выполнить:

```powershell
uv run --group training python -m projects.document_intelligence_lab.external_model_study.pretrained_smoke --cache .cache/roadmap-huggingface --output generated-reports/minilm-author-pretrained-smoke
```

Команда сама сеть не использует: сначала проверяет весь закреплённый cache,
берёт по одному настоящему тексту каждого intent, загружает реальный `AutoModel`,
показывает padding-safe pooling, сохраняет safetensors и сравнивает hidden states
после локального reload. Это **четырёхстрочный inference/save/load walkthrough**,
а не сравнение качества или learner submission. Маркер
`AUTHOR_PRETRAINED_INFERENCE_SMOKE_ONLY`, `learner_credit=NOT_GRANTED` и
`quality_evaluation=NOT_RUN` сохраняют эту границу даже при правильных pinned weights.
Ни полноценная адаптация, ни оценка final holdout этой командой не выполняются.
Без скачанного cache получаете явный отказ до создания output, без скрытого download.
