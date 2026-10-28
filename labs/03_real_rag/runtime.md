# Явные runtime gates R07

Проверено 2026-10-11: базовая среда выполняет lexical/contracts tests; training среда
выполняет local random shapes. В отдельно выбранной `.venv-rag` установлен
`qdrant-client==1.19.1`; **actual local Qdrant mechanics/persistence: PASS**.
После отдельного разрешения пользователя скачаны только шесть pinned MiniLM files
(91 567 205 bytes); Bitext не скачивался. **Pretrained CLS retrieval: MEASURED**
на маленьком teacher corpus; **LLM quality: NOT_RUN**. Серверы не запускались.
Ранний hand-vector опыт остаётся механизмом, не зачётом ученика. Проверенные
наблюдения и ограничения — в [протоколе запуска](verification.md).

В [dense.py](dense.py) есть lazy boundary для `QdrantClient(path=...)`, только local disk.
Нет URL, Docker, облака, FastEmbed или model-name inference. Обычный pytest не
вызывает Qdrant smoke. Явный вызов без runtime завершается RuntimeError / NOT_RUN;
без assets encoder завершается ошибкой actual artifact verification до загрузки модели.

Повторяемый опыт без encoder и без скачиваний, из корня, в подготовленной среде.
Выберите **новые** snapshot/storage пути: повторное использование отвергается.

```powershell
$snapshotReceipt = .venv-rag/Scripts/python.exe -m labs.03_real_rag.dense hand-snapshot --output artifacts/r07-hand-new | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'hand snapshot failed' }
.venv-rag/Scripts/python.exe -m labs.03_real_rag.dense qdrant-smoke --storage artifacts/r07-qdrant-new --snapshot artifacts/r07-hand-new --manifest-sha256 $snapshotReceipt.snapshot_sha256
if ($LASTEXITCODE -ne 0) { throw 'Qdrant smoke failed' }
# Новый python process открывает уже закрытый index:
.venv-rag/Scripts/python.exe -m labs.03_real_rag.dense qdrant-verify --storage artifacts/r07-qdrant-new --snapshot artifacts/r07-hand-new --manifest-sha256 $snapshotReceipt.snapshot_sha256 --receipt artifacts/r07-qdrant-new/fresh-process-receipt.json
```

`hand-snapshot` сохраняет четыре разрешённых автором synthetic passages из
`fixtures/corpus.json`, существующий контракт chunk IDs и manifest sizes/SHA-256.
Identity называется `HAND_AUTHORED_API_GEOMETRY_NOT_EMBEDDINGS`: pooling отсутствует,
размерность 2, query `[1,0]`. Это не вызов embedding модели и не retrieval benchmark.
`qdrant-smoke` пишет `mechanics-receipt.json` после успешного close/reopen; отдельный
`qdrant-verify` сверяет disk points, а не доверяет этому receipt. Он проверяет
dimension/cosine, snapshot+embedding identity в collection metadata, **полный набор
ID, exact payload и численные vectors**, затем public query. Отдельный receipt
содержит PID, версию, inventory digest и фактическое время одной проверки.
Время одного запуска не равно p95 latency; стоимость, память и семантика не измерены.

Для отдельных integration tests нужен явный gate; обычный pytest даже с установленным
клиентом их пропускает. Gate без установленного пакета приводит к failure, не PASS.
Lab fixture запрещает socket connections и downloads; эти тесты работают на диске.

```powershell
$env:ROADMAP_RUN_QDRANT = '1'
.venv-rag/Scripts/python.exe -m pytest labs/03_real_rag/test_qdrant_runtime.py -q
Remove-Item Env:ROADMAP_RUN_QDRANT
```

Другой, отдельно выбираемый маршрут использует **уже существующие** проверенные
pretrained assets. Этот путь выполнен на CPU; для собственного повтора выбирайте новые папки:

```powershell
.venv-training/Scripts/python.exe -m labs.03_real_rag.dense encode-local --model-dir .cache/roadmap-huggingface/model --output artifacts/r07-dense-new
# Qdrant работает в уже существующей отдельной retrieval-среде, Torch ей не нужен:
.venv-rag/Scripts/python.exe -m labs.03_real_rag.dense qdrant-smoke --storage artifacts/r07-pretrained-qdrant-new --snapshot artifacts/r07-dense-new --manifest-sha256 ACTUAL_DIGEST_PRINTED_BY_ENCODER
```

`ACTUAL_DIGEST_PRINTED_BY_ENCODER` — значение из собственного запуска, не готовый hash.
Первый путь — уже существующий allowlist модели из HF lab; не требуется скачивать
не относящийся к RAG account dataset. Веса проверяются по size/SHA-256, model ID и
revision из [существующего resources.json](../02_huggingface_models/resources.json).
Папка модели должна содержать **ровно** перечисленные обычные файлы: дополнительные
`added_tokens.json`, `adapter_config.json`, любые вложенные каталоги и file links
отвергаются до `from_pretrained`. Иначе loader мог бы потребить bytes, которые
не входят в inventory identity. Не удаляйте лишние пользовательские файлы ради
прохождения проверки: отдельно подготовьте новую папку с проверенными allowlist bytes.
Политика exact directory записывается в embedding identity и затем snapshot manifest.
Проверка предполагает operator-controlled папку без конкурентного изменения между
проверкой и загрузкой; hash не устраняет этот filesystem race.
Обе `from_pretrained` получают local Path, `local_files_only=True`,
`trust_remote_code=False`; model также `use_safetensors=True`. Batch≤8, max_length=128,
CPU и eval/inference mode записаны в embedding identity. Pooling **CLS**, не
рекомендованный model-card mean pooling; качество надо измерить самостоятельно.

Encoder сохраняет snapshot sources/chunks/vectors и два top-k списка с per-query
Recall/MRR в `retrieval-comparison.json`. Он связывает comparison с digest snapshot
и исходных judgments. Snapshot manifest связывает exact corpus/vector bytes,
dimension, модель/revision/file inventory, pooling и preprocessing. `load_snapshot`
требует operator-selected manifest digest, проверяет bytes и source/chunk соответствие.
Comparison report — наблюдение явного teacher run, не ученический отчёт; его ручной
разбор остаётся `REQUIRES_REVIEW`. На трёх answerable queries CLS действительно
нашёл релевантный chunk первым; lexical пропустил paraphrase. Это наблюдение пяти
заранее заданных случаев, не гарантия переноса на другой corpus. На absent/protected
queries dense также возвращает public соседей: cosine не доказывает наличие ответа.

Разрешение было **только на модель**. Обычный downloader lab02 по умолчанию получает
ещё и Bitext, поэтому он в этом опыте не запускался. Были вызваны существующие
`resource_manifest` и `fetch_verified` только для `manifest["model"]["files"]`:
каждая передача ограничена pinned size и timeout=60s, итог проверен по SHA-256,
существующие неправильные bytes не перезаписываются. Последующие `encode-local`
используют только уже сохранённые `.cache/roadmap-huggingface/model` bytes.
`pytest`/`uv sync` не скачивают модель даже после этого разрешения.

Важно: старый `qdrant-smoke` **всегда mechanisms-only**, в том числе с MiniLM vectors:
он намеренно переиспользует vector после изменения HOURS text. Его index нельзя
подавать generator как готовый semantic release. Для корректного обновления
в новом B snapshot HOURS был заново encoded, SCAN revoked, APPENDIX удалён;
согласованный restore описан в [локальном R09](../06_ml_lifecycle/coupled-recovery.md).

В разобранном опыте private `A-STAFF` имеет cosine 1.0, public `A-SCAN` — примерно
0.993884. Без фильтра top-1 был бы staff; `query_filter` до `limit=1` возвращает
разрешённый `A-SCAN`. Затем `set_payload(access=staff)` убирает его из public query,
delete удаляет его ID. Другой source `A-HOURS` получает новую revision, text, digest
и chunk ID; старый ID удаляется. Используется прежний ручной vector `[0,1]` — это
демонстрация API, а не корректное переэмбеддирование изменённого текста.

```text
4 points: 3 public + 1 staff
    → revoke SCAN: 2 public + 2 staff
    → delete SCAN: 3 points
    → HOURS revision replacement: 3 points
    → close → reopen → fresh process: 3 current IDs
```

Smoke требует два разных public sources; это фиксированная teacher mutation.
`qdrant-verify` отказывает при появлении удалённого SCAN, старого HOURS, другой
dimension или embedding inventory. Отдельные actual tests намеренно вносят такие
ошибки в свои temporary indices. Рецепт изменяет только собственный новый storage;
не применять его к существующему production index. Local disk mode — не проверка
server ANN, multi-client concurrency, crash recovery или транзакционной публикации.

Для полноценного ingestion/update pipeline: используйте выполненный `rag-index-sync`
как план, `rag-text-chunking` как контракт; embed только новые/изменённые chunks,
удалите все obsolete IDs изменённого/удалённого source. Публикуйте новый согласованный
corpus/embedding/index snapshot после завершения; при частичном сбое не переключайте
активную версию. Рецепт выше проверяет revoke/delete/persistence, но не реализует
production transactional ingestion или общий sync solver вместо student TODO.
Смена model/tokenizer/pooling/max_length меняет representation identity; re-embed
весь корпус в новой коллекции и повторите queries. После restart проверьте выдачу,
metadata и отсутствие старых/удалённых chunks, не только наличие папки.
Перед generator остаётся обязательной повторная проверка against current source:
revision, digest, text и текущие права, как в `rag.assemble_context`/`answer_query`.
Qdrant payload ACL не заменяет эту проверку при изменении источника между query
и сборкой контекста. Smoke generator не вызывает.

Самостоятельная вариация: задайте другую ручную query direction, заранее вычислите
ожидаемый public top-1, затем проверьте actual выдачу. Отдельно измените revision
двухабзацного source и объясните, какие старые ID должны исчезнуть. Решение и
ученический отчёт не входят в авторский trace; используйте existing exercise IDs.

Generator выбирается отдельно. Локальный excerpt callable позволяет проверять
маршрутизацию и ошибки без LLM. После авторизованного запуска
[R08 serving](../05_model_serving/README.md) замените его адаптером к явно выбранному
endpoint: передавайте только authorized current context, ограничьте deadline,
output tokens/characters и число retries; outage отображайте в `ProviderUnavailable`.
Сопоставляйте утверждения с quotes и source revision, фиксируйте no-answer причины.
Наличие citation ID не является grounded evaluation; ручная рубрика обязательна.
Не отправляйте staff bytes или corpus целиком ради «проверки безопасности».

Запись результата должна различать author mechanism PASS, actual integration
PASS/NOT_RUN, retrieval metrics + scope, answer review REQUIRES_REVIEW, student status.
Latency/cost/memory до измерения — null с причиной либо NOT_MEASURED; не подставлять
синтетические миллисекунды. Полный R07 Done требует настоящий совместимый encoder,
постоянный Qdrant, generator и независимую retrieval/answer evaluation.
