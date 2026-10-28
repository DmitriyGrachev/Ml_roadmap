# Контракт classification bundle, schema 1

Общий код проекта: [contracts.py](../contracts.py) и [artifacts.py](../artifacts.py).
Его используют A1 и дальнейшая доставка CPU; никаких downloads при импорте нет.
`write_run_new` создаёт новый каталог и возвращает `manifest.json`.
Существующий output вызывает `FileExistsError` без изменения старых bytes.

| Файл / logical artifact | Обязательный смысл |
| --- | --- |
| `data.json` / `data` | `schema_version=1`, ordered `labels`, ordered `records` |
| `splits.json` / `splits` | Только `train`, `validation`, `test`, ordered nonempty IDs |
| `sources.json` / `sources` | source ID, permission, license, annotation policy |
| `model.json` или `model.pkl` / `model` | Полная модель и её preprocessing |
| `predictions.json` / `predictions` | Ordered `{row_id,predicted_label}` для ровно test IDs |
| `metrics.json` / `metrics` | count, accuracy, macro_f1, confusion, label_order, zero_division |
| `errors.json` / `errors` | Все фактические ошибки, true/predicted label и review status |
| `measurement.json` / `measurement` | Измеренные timings и memory либо причина неизвестности |
| `selection.json` / `selection` | criterion, saved candidate `selected_method`; optional comparison winner |

`records` содержит только `row_id,text,label,source_id,group_id,content_sha256`.
Text hash = SHA-256 точных UTF-8 bytes текста. ID уникальны, labels известны,
text непустой. Split — точное разбиение всех accepted rows; ID и группы не пересекаются.
Нормализованные точные повторы между split запрещены: NFKC → casefold → collapse
whitespace. Эта проверка не обнаруживает смысловые пересказы и общие шаблоны.
В teacher наборе словарь намеренно общий; это ограничение synthetic smoke.

JSON writer использует UTF-8, sorted keys, `allow_nan=False`, один завершающий newline.
Исходные `data/splits/sources` копируются побайтно; их identity относится к bytes,
поэтому даже изменение форматирования меняет SHA-256 файла.

Manifest: `schema_version=1`, `exercise_id`, `dataset_sha256`, `split_sha256`,
`config` с целочисленным seed, `method`, `evidence_kind`, `run_id`, ordered `labels`;
`code={revision,dirty,source_sha256}`; `versions`; `preprocessing={id,version,config}`;
`model={id,revision,format}`; `artifacts={logical:{path,sha256,size_bytes}}`.
Manifest не содержит свой digest: ожидаемый SHA-256 готового manifest хранится снаружи.
Teacher source hash связывает UTF-8 relative filename, NUL, фактические bytes, NUL
для `contracts.py`, `artifacts.py`, `part_a1/demo.py` в таком порядке.

Preprocessing `unicode-whitespace-v1`, version `1`, config `{}` — NFKC/casefold/whitespace.
У sklearn fitted vectorizer включён в Pipeline; параметры и IDF находятся в pickle.
Единственный поддержанный sklearn формат — `sklearn-pickle-v1`: Pipeline из
TfidfVectorizer + LogisticRegression. Нужны совпадающие sklearn/numpy/scipy versions
и Python major.minor. Будущий encoder требует явного нового adapter, не remote fallback.

JSON `rules-json-v1`: `{schema_version:1,labels:[...],rules:[{token,label}],fallback_label}`.
Первая rule с точным нормализованным токеном выигрывает, иначе fallback.
Никаких confidence/probability этот формат не обещает.

Истина берётся только из data. Метрики используют весь ordered label universe;
confusion rows = true label, columns = predicted label; undefined F1 = 0.
Error rows имеют category `misclassification`, analysis status `REQUIRES_REVIEW`.
Метрики и список ошибок пересчитываются; произвольная self-reported truth колонка запрещена.
Текстовое объяснение ошибки всё равно оценивает человек.

Timing row: `name,value,unit='seconds',device='cpu',sample_count,batch_size,condition`;
condition — cold или warm, value — измеренное конечное неотрицательное число.
Memory — `memory_bytes: null` + nonempty `memory_unknown_reason`, либо измеренные bytes.
Проверка структуры не доказывает честность времени; instrumentation нужно защищать.

Минимальный API для заранее выбранного оператором bundle:

```python
verified = verify_bundle(root, expected_manifest_sha256=operator_digest)
classifier = load_trusted_local_classifier(root, operator_digest, trusted_local_artifact=True)
labels = predict_documents(classifier, ["small blue circle"])
```

`verify_bundle` проверяет inventory/bytes/schema/данные/метрики и safe JSON rule schema,
не исполняя pickle. Можно дополнительно передать внешние ожидаемые
`exercise_id`, `dataset_sha256`, `split_sha256` для фиксированного study.
`load_trusted_local_classifier` также replay test predictions; JSON rules не требует
trusted flag, pickle требует буквальный `True` и совместимую среду перед deserialization.
`predict_documents` принимает 1–128 текстов по 1–10000 символов, возвращает canonical labels.

Returned `VerifiedBundle`: root, manifest_sha256, manifest, dataset, splits, predictions,
paths. Dataset/Record immutable; manifest — прочитанные metadata.
`LocalClassifier` содержит `.bundle` и `.model`. API request не выбирает пути, digests,
URLs или trust flag. Directory/config должны быть защищены оператором от замены во время
проверки: проверки путей и hash не решают concurrent tampering и не создают sandbox.
