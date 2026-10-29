# Token classification: subwords, BIO и точные сущности

ID: `lab-token-classification`. Optional group: `trainer`. Это отдельная
лабораторная NER после [основной lab02](../README.md) и
[Trainer workflow](../trainer_workflow/README.md). Нужны tokenizer/attention masks,
cross-entropy, validation и признаки утечки между splits. Все learner функции
в [starter.py](starter.py) остаются TODO.

```bash
uv sync --group trainer
uv run --group trainer python -m labs.02_huggingface_models.token_classification.example
uv run --group trainer python scripts/learn.py test lab-token-classification
```

Author smoke создаёт словарь и BERT случайно (1 блок, hidden=16), collator,
настоящий token-classification loss, одно AdamW обновление на CPU в одном потоке,
затем safe save/local reload через `AutoModelForTokenClassification`. Это
**RANDOM_LOCAL_MECHANICS_ONLY**, не pretrained NER и не качество на новом домене.
Путь `artifacts/ner-author-smoke/` должен быть новым; для повторного запуска задайте
новый `--output`. Артефакты игнорируются git; import ничего не запускает. pytest
проверяет только ограниченную локальную механику и не скачивает ресурсы.

## Разметка и схема

В [fixtures.json](fixtures.json) — авторский нейтральный английский текст.
`train` — посещение/заметка; `validation` — встреча; независимое расширение
`test` — выставка/архив. Это **учебная иллюстрация** разных формулировок, не
доказательство статистической независимости или репрезентативный корпус.
Heldout расширение уже открыто читателю: оно не годится для честной новой оценки,
если использовалось при исправлении модели. Для learner credit создайте свои
семейства текстов и независимый heldout, не заменяйте только имена в шаблоне.

Одна строка: `{id, words: list[str], tags: list[str]}`. Длины words и tags равны.
`LABELS`: `O, B-PER, I-PER, B-LOC, I-LOC, B-ORG, I-ORG` в этом порядке.
PER — личное имя; LOC — географическое место; ORG — именованная организация.
Точки/запятые отдельно и O. Титулы вне сущности; многословные названия включают
все слова (`New York` → B-LOC I-LOC). «Cedar Press» как издатель — ORG; обычное
«cedar press» как предмет было бы O. Кавычки не входят в сущность.
Эта политика нужна до обучения: accuracy не исправляет противоречивую разметку.

| Слово | Токен | word_id | Word BIO / ID | Train label |
| --- | --- | --- | --- | --- |
| — | `[CLS]` | None | — | -100 |
| Ada | `ad` | 0 | B-PER / 1 | 1 |
| Ada | `##a` | 0 | B-PER / 1 | -100 |
| visits | `visits` | 1 | O / 0 | 0 |
| Rome | `rome` | 2 | B-LOC / 3 | 3 |
| . | `.` | 3 | O / 0 | 0 |
| — | `[SEP]` | None | — | -100 |
| — | `[PAD]` | None | — | -100 |

Это точные значения локального smoke tokenizer, не обещание такой сегментации
у другой модели. `word_ids()` относится к pretokenized словам. Задайте
`is_split_into_words=True`, fast tokenizer, используйте **каждую** строку batch
с её `batch_index`. Индексы не являются character offsets. Для показа исходных
символов храните offsets отдельно; не собирайте текст простым удалением `##`.

## Учебные boundaries

`align_labels(word_ids, word_labels) -> list[int]`: первое появление слова получает
исходную метку, следующие фрагменты — -100. Special tokens — -100. Пустой и
all-special список допустимы. Отвергайте отрицательные, bool, выход за длину
word_labels, возврат назад, пропуск ещё не встреченного ID и повторное слово
после None. ID первого реального слова — 0. Например `[None,1]` — orphan window,
а `[0,None,0]` — оборванная группа. Одинаковые соседние IDs — нормальные subwords.
Не превращайте B-PER в I-PER для продолжений: наша loss policy их исключает.

Сам список word_ids не сообщает, был ли отрезан **последний** фрагмент слова.
Runner должен сравнить offsets/полную токенизацию с truncated версией и исключить
неполную сущность. Оконные chunks с продолжением первого слова отбрасывайте или
строите на границе слова; не назначайте ему новую B метку без аудита. Если
truncation удаляет всё после `B-PER` перед `I-PER`, entity уже неполная, хотя
первый label остался. `entity_coverage(tags, complete_word_ids, supported)` явно
считает entities, supported_complete, truncated_entities, unsupported_entities.
Два последних счётчика могут пересекаться. Передавайте **полные** word IDs,
а не все IDs, присутствующие хотя бы одним subword. Ограничение support нужно
для переноса на snapshot, у которого нет определённых типов; runner учебного
контракта требует нашу полную mapping, а аудит других mappings ведётся отдельно.

`entity_metrics(predictions, references)` получает **отдельные предложения** с
BIO strings после снятия -100 и восстановления слов. Strict policy: I-X должен
следовать B-X/I-X того же типа. Invalid I в reference или prediction — ValueError;
не «чините» его незаметно в B. На inference отдельно запишите число invalid
переходов, исходные logits и решение о constrained decoding; метрики подавайте
только на валидную последовательность. Не соединяйте предложения. Возврат:
`precision, recall, f1, tp, fp, fn`; нулевой denominator даёт 0.0.

Точная сущность — `(тип, начало_слова, конец_исключительно)`. Gold
`[B-PER,I-PER,O]` и prediction `[B-PER,O,O]`: TP=0, FP=1, FN=1. Тип совпал,
граница — нет. Если другая сущность угадана точно, TP=1 и precision=recall=1/2.
Счётчики суммируются по предложениям, затем считаются micro P/R/F1. Token accuracy
на O не заменяет entity F1; один длинный O-фрагмент может скрыть все пропущенные
имена. Не считайте -100 как правильные O. Для all-ignored строки метрик сущностей
нет; счётчики нулевые. Для all-ignored **training batch** пропустите обновление
с явным счётчиком: mean CrossEntropyLoss без активных labels неопределена.

`train_token_classifier(model, tokenizer, splits, output, max_steps=2, *, max_length=32, batch_size=2)` обучает
переданную actual `AutoModelForTokenClassification`, используя обе learner
функции. Проверьте split IDs, labels/config до forward. Настоящие
`Dataset.map` + `DataCollatorForTokenClassification(label_pad_token_id=-100)`;
padding=True динамически, обучение CPU с ручным бюджетом 1..100 optimizer steps, seed записан, report_to
none. Validation выбирает checkpoint; heldout используется после выбора. Возврат:
`predictions`, `references` (word BIO по строкам test), `span_metrics`, `coverage`,
`split_ids`, сырая `history`, `checkpoint_path`, `model_identity`, `reload_identity`,
`tokenizer_identity`, `optimizer_steps`, `skipped_all_ignored_batches`.
Сохраните также исключённые строки/сущности, полные labels, subword predictions,
настройки truncation и отдельно число all-ignored batches. Identity — SHA-256
имён/CPU bytes параметров в фиксированном порядке; reload local safe, logits
одинаковы в eval. Не используйте авторский smoke вместо этой функции.

## Кривые и разбор ошибок

Train loss усредняется по активным токенам, entity F1 — по целым spans; их масштабы
не совпадают. Loss может снижаться на O, пока recall редких ORG не меняется.
Сохраняйте по validation step loss, span TP/FP/FN, F1 и количество исключений.
Лучший F1 выбирается по validation, критерий фиксируется заранее. Падение F1 на
одной длинной сущности в маленькой выборке не позволяет заключить о деградации
языковой модели. Не дорисовывайте кривые для двух шагов; таблица сырых логов
честнее. При train↓ / dev loss↑ проверьте overfit, несовпадение entity policy и
split семьи; при обеих loss неподвижных проверьте labels dtype, -100, train mode,
requires_grad, optimizer.zero_grad и реальные изменения параметров.

## Локальный learner experiment и human review

Загрузите выбранный pretrained snapshot **отдельно** с pinned revision; import,
pytest и runner сеть не используют. Шаблон явного действия:

```bash
hf download YOUR_TOKEN_CLASSIFIER --revision EXACT_REVISION --local-dir .model-cache/ner-source
```

Подготовьте локальный snapshot с exact LABELS mappings и safetensors. Если
исходная модель использует другие типы/порядок IDs, сначала документированно
переобучите/подготовьте голову; не меняйте config имена без переноса строк весов.
Изучите лицензию/card и сохраните repo/revision, язык, предназначение, ограничения.
JSON: `{dataset_source, model_source, splits}`. Sources включают revision/license
и преобразования. Fixture не является вашим живым dataset.

В review.md перечислите новый домен/авторство, минимум две неоднозначные границы,
один неправильный type и одну пропущенную entity, supported/truncated counts,
почему heldout независим по семьям. Второй человек должен просмотреть хотя бы
пять примеров, включая пунктуацию, многословное имя, subword и усечение; запишите
замечания и исправления. Поле human_review само по себе review не доказывает.

```bash
uv run --group trainer python -m labs.02_huggingface_models.token_classification.run \
  --snapshot .model-cache/ner-source --dataset data/my-ner.json \
  --review data/my-ner-review.md --output artifacts/ner-learner
uv run --group trainer python scripts/learn.py check lab-token-classification
```

Runner сохраняет provenance входных bytes, predictions/span metrics и reload
identity. Default strict artifact `artifacts/ner-learner/report.json` отсутствует
в чистом checkout, поэтому untouched TODO/xfail/author smoke не дают completion.
Human проверяет данные и модель: нельзя автоматически доказать, что локальные
bytes pretrained или review действительно выполнен. Ошибки не записываются как
успешный report. Перенос освоен, когда вы можете восстановить каждый word label,
объяснить каждую маску и FP/FN по границам, назвать потерянные при truncation
сущности и воспроизвести сохранённую модель на собственном heldout.

### Бюджет, all-ignored и retained checkpoint

Author smoke остаётся <=4 optimizer steps, а явный ручной learner эксперимент
допускает 1..100 (default=2); это возможность более содержательной практики,
не гарантия качества. CLI принимает `--steps`, `--max-length` и `--batch-size`.
Неверные значения и bool отвергаются до обучения; тесты используют максимум
одно активное обновление в дополнительном NER случае, а не длинные прогоны.
Если используется Trainer, `save_total_limit=2`; сохраняйте не больше двух
checkpoints плюс выбранный export.

`coverage` относится к test после truncation, сохраняя исходные entity spans:
entities, supported_complete, truncated_entities, unsupported_entities. Полностью
усечённая или частично оставленная сущность исключается из references/scoring;
в training также замаскируйте retained фрагмент неполного слова через -100.
Например Lee + Ada при WordPiece lee/ad/##a и max_length=4 даёт
`[CLS],lee,ad,[SEP]`, labels `[-100,1,-100,-100]`; Ada считается truncated.
При max_length=2 остаются special tokens: пропустите batch до model loss,
увеличьте skipped_all_ignored_batches, не вызывайте backward/optimizer step.
Если все train batches ignored, закончите один проход с optimizer_steps=0 и
неизменными весами; не повторяйте пустые эпохи до достижения max_steps. Это
диагностический результат, который сам по себе live completion не даёт.

Live report обязан содержать disjoint train/validation/test split_ids, predictions
и references в порядке test IDs, raw validation history с step/eval_loss/eval_f1.
Strict gate повторно загружает checkpoint и fast tokenizer локально, сверяет
фактические fingerprints и выполняет короткий inference. Tokenizer fingerprint
фиксирует vocabulary, normalizer/special-token semantics и стороны padding/truncation.
Удалённые/изменённые веса или tokenizer не заменяются равными строками в JSON.
