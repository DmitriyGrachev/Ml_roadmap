# Локальное восстановление coupled release

`coupled.py` позволяет совместно выбрать две учебные ветки: classification release
и RAG corpus/snapshot с точными шестью файлами MiniLM. У классификатора свои
dataset, labels, preprocessing и model; у retrieval — свои sources, revisions,
chunks, embedding и index. Совместный выбор не означает, что classification dataset
совпадает с RAG corpus или что улучшение одной ветки улучшает другую.

Проверка model files подтверждает bytes и inventory, но не доказывает, что именно
этими файлами были вычислены сохранённые vectors. Для подтверждения реального
pretrained запуска отдельно сохраняйте encoder receipt с provenance.

## Что связывает release

Внешний `coupled-release.json` закрепляет nested classification release pin,
snapshot pin, corpus/vector digests, полную embedding identity, UUID5 chunk point
IDs, cosine configuration и текущие lifecycle source/Python/NumPy identities.
Verification требует совпадающей реализации и точных версий Python/NumPy. Это
намеренно узкий локальный контракт: после изменения source code или runtime старый
release нельзя объявлять совместимым только по наличию файлов.

Храните outer pin во внешней operator configuration. Вычислить digest из
непроверенного каталога и тут же довериться ему — не то же самое, что независимо
выбрать известный release. Classification schema 1 и прежний dense snapshot/smoke
contract остаются прежними.

```text
classification release ── release pin + bundle bytes ──┐
RAG snapshot ── snapshot pin + sources/chunks/vectors ─┼─ write → coupled release
MiniLM ── exact 6 files + full embedding identity ────┘
                                                        │ verify: bytes/compatibility
                                                        ▼
                                      restore в новой папке, base process
                                      ASGI readiness + actual classifier inference
                                                        │
                                                        ▼
                                      index в новой storage, отдельный rag process
                                                        │ закрыть local client
                                                        ▼
                                      verify-index в fresh process
                                      IDs + payloads + vectors + config + metadata

artifacts/
├─ coupled-A/
│  ├─ coupled-release.json
│  ├─ classification/
│  │  ├─ release.json
│  │  └─ bundle/…
│  ├─ snapshot/{manifest,sources,chunks,vectors}.json
│  └─ model/  [6 pinned files]
├─ recovered-A/  [та же структура + recovery.json + classification/restart.json]
├─ recovered-A-index/  [Qdrant storage, collection coupled_author]
└─ …-write.json / …-verify.json / …-reopen.json  [внешние CLI receipts]
```

Все output directories и CLI receipt files должны быть новыми. Размещайте CLI
receipts вне всех input/output artifact directories и index storage. Symlinks,
junctions и связанные через них ancestor paths запрещены, включая все descendants
уже существующей index storage: проверка происходит до открытия Qdrant. Защитите локальные
каталоги от одновременной подмены. При ошибке после копирования или runtime startup
частичный output сохраняется для осмотра; повторная попытка требует новой папки.

## Пример наблюдения A → B → A

Ниже — результаты фактического локального авторского запуска. Это сравнение
восстановленных состояний и parity, а не оценка качества или production rollback.

| Выбранное состояние | Classifier для `triangle` | Полный index inventory | Public chunks в snapshot | Наблюдение corpus |
| --- | --- | --- | --- | --- |
| A | `circle` | 4 chunks | 3 | Исходные revisions и исторические ACL |
| B | `triangle` | 3 chunks | 1 | `A-HOURS@2:p1`: закрытие в 15:00; SCAN revoked, APPENDIX deleted |
| Снова A, в новой recovery/storage | `circle` | Те же 4 chunks, что у A | Те же исторические 3 | Подтверждена parity с A; актуальные права этим не восстановлены |

Внешние SHA256 pins повторного запуска v2 после усиления path preflight:

```text
A: 2366d8ffcf02d0aeb8c44104f02bad2c3d0d5108a35606da260291c210ade72b
B: a02c0173adde267a0e9212548a7b82d8060407fa15f4024f007779521179f373
```

Artifacts v1 оставлены как исторические; изменение code identity требует нового
release, а не перезаписи старого. Текущие receipts и ограничения — в
[проверках](verification.md#coupled-local).

Различие `circle`/`triangle` — наблюдение classifier inference; число chunks и их
revisions — наблюдение retrieval state. Из этого не следует улучшение accuracy,
retrieval quality или answer quality. Для нового B corpus нужны собственные
judgments: старую разметку с прежними chunk IDs нельзя использовать как валидную
оценку B. Generator в manifest равен `null`, generation — `NOT_RUN`.

Исторический snapshot содержит исторические access metadata. Возврат A после B
может снова показать SCAN как public только в этих синтетических привилегированных
operator parity checks. Восстановление snapshot не разрешает выдавать документ по
его старым правам. Перед user-facing serving или generator call проверяйте live
authoritative ACL и current source; храните revocation tombstones и authorization
policy отдельно от rollback artifacts. Этот helper не реализует live authorization
layer и не запускает публичный server/generator.

## Практический запуск

Замените placeholders независимо записанными SHA256 и своими путями. Примеры ниже
используют условные имена каталогов; pins A/B выше относятся только к конкретным
авторским artifacts. В PowerShell замените `<…>` до выполнения команд.

Source snapshot может содержать `retrieval-comparison.json` и `query-evidence.json`
с encoder observations: они не копируются и не становятся доверенными release
constituents. Другие незаявленные входные файлы отклоняются.

```powershell
.venv-base-check/Scripts/python.exe -m labs.06_ml_lifecycle.coupled write `
  --classification-release artifacts/classification-A `
  --classification-release-sha256 <CLASSIFICATION_PIN> `
  --snapshot artifacts/snapshot-A --snapshot-sha256 <SNAPSHOT_PIN> `
  --model-dir .cache/roadmap-huggingface/model --output artifacts/coupled-A `
  --receipt artifacts/coupled-A-write.json

.venv-base-check/Scripts/python.exe -m labs.06_ml_lifecycle.coupled verify `
  --root artifacts/coupled-A --release-sha256 <OUTER_PIN> `
  --receipt artifacts/coupled-A-verify.json

.venv-base-check/Scripts/python.exe -m labs.06_ml_lifecycle.coupled restore `
  --root artifacts/coupled-A --release-sha256 <OUTER_PIN> `
  --output artifacts/recovered-A --receipt artifacts/recovered-A-restore.json
```

Для operator-trusted local sklearn pickle добавляйте `--trusted-local-artifact`
только к `restore`. Совпавший digest не даёт права доверять pickle. Restore повторно
использует существующий service startup и проверяет реальные in-process ASGI
readiness/inference; nested `classification/restart.json` и внешний `recovery.json`
фиксируют эту область проверки. Base verification не импортирует
torch/transformers/Qdrant и не вызывает encoder/model download.

Index commands выполняются отдельно в уже подготовленном retrieval environment:

```powershell
.venv-rag/Scripts/python.exe -m labs.06_ml_lifecycle.coupled index `
  --root artifacts/recovered-A --release-sha256 <OUTER_PIN> `
  --storage artifacts/recovered-A-index --receipt artifacts/recovered-A-index.json

# Start a fresh process after the index writer closes its local client.
.venv-rag/Scripts/python.exe -m labs.06_ml_lifecycle.coupled verify-index `
  --root artifacts/recovered-A --release-sha256 <OUTER_PIN> `
  --storage artifacts/recovered-A-index --receipt artifacts/recovered-A-reopen.json
```

Collection называется `coupled_author`. Восстановление берёт исходные points из
snapshot, а не прежний delete/update smoke plan. Reopen проверяет точные point IDs
и payloads, numeric vectors с float persistence tolerance `atol=rtol=1e-6`,
dimension, cosine distance и release/snapshot/representation/config metadata.
Fixed first-public-chunk self-query применяет public ACL до top-k и проверяет
score parity; это не retrieval-quality metric и не проверка актуальности ACL.

## Как читать ошибку

| Ситуация | Что означает отказ |
| --- | --- |
| Не совпал внешний pin или изменились model/corpus bytes | Нельзя подтвердить выбранное состояние; не подставляйте digest повреждённой копии |
| Dimension прежняя, но изменён pooling или `max_length` | Representation несовместима; одинаковой размерности недостаточно |
| В model появились дополнительные loader files | Exact inventory нарушен; произвольные inputs не копируются |
| Source code или Python/NumPy versions отличаются | Текущий узкий runtime contract не подтверждает совместимость release |
| Output/receipt уже существует либо вложен в pinned input | Нужен новый внешний destination; повторное использование не происходит |
| Pickle не получил explicit trust | Проверка bytes не разрешает executable deserialization |
| Point count верный, но изменены payload/vector/metadata | Persisted index не соответствует snapshot; одного count недостаточно |

Receipts содержат PID, UTC time, выбранные pins, versions и elapsed wall time.
vLLM остаётся `DEFERRED_ENV`. Здесь проверены local persistence и in-process service
recovery; remote server, ANN, crash safety, registry promotion и atomic switching
не запускались. Если runtime не подготовлен, сохраняйте честный `NOT_RUN`.

## Предскажите перед запуском

1. Если оставить dimension 384, поменять только `max_length` и заново вычислить
   outer digest, какая проверка ещё нужна для совместимости и почему?
2. Если после restart число points совпало, но у одного point остался старый
   revision в payload, какое наблюдение отличит это от корректного восстановления?
3. Если B отозвал доступ, а snapshot A хранит прежний public ACL, какие данные
   должны определять право user-facing ответа после восстановления A?

## Независимая вариация без готового решения

Используйте собственный завершённый classifier bundle и разрешённый небольшой
corpus из другой предметной области. Подготовьте две revisions с одним изменением
содержимого и одним изменением access; teacher shapes, corpus и judgments не
переносите. До запуска запишите прогноз: какие predictions, IDs, payloads и
preflight checks должны измениться, а какие наблюдения ещё не доказывают quality.

В новых экспериментальных папках выберите original/candidate и восстановите
original в отдельную recovery/storage. Добавьте один случай несовместимости только
в расходной копии, сохранив originals. Сопоставьте прогноз с actual receipts,
полным inventory и readiness/inference; отдельно объясните судьбу live ACL при
возврате исторического snapshot. Не меняйте пороги после просмотра результатов,
не удаляйте реальные данные и не устанавливайте runtime ради заполнения отчёта.

Продолжите существующую [lifecycle variation](exercise/README.md) и
[RAG variation](../03_real_rag/exercise/README.md), соблюдая их prerequisites.
Собственные evidence и ограничения внесите в
[lifecycle report](exercise/report-template.md) и
[RAG report](../03_real_rag/exercise/report-template.md). Разметка revised corpus,
выбор generator и оценка answers остаются самостоятельной работой; эта страница
не содержит их решения. Результат оценивается вручную: `REQUIRES_REVIEW`.
