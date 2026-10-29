# Real RAG: корпус, индекс и проверяемые основания ответа

CORE Applied AI. Авторские offline материалы подготовлены;
actual local Qdrant persistence/ACL/update/delete — **PASS**.
MiniLM CLS retrieval на пяти фиксированных teacher queries — **MEASURED**:
[наблюдения и ограничения](verification.md#minilm-local). Это не общий benchmark.
Первый Windows/Ollama Qwen2.5 teacher smoke — **MEASURED**:
[ответ, задержки, явный запуск и ограничения](../../docs/local-generator-verification.md).
Он использует lexical retrieval; dense+LLM и полноценная answer evaluation — **NOT_RUN**.
Это не выполненный ученический зачёт.

Prerequisites: [Hugging Face](../02_huggingface_models/README.md),
[модуль 06](../../modules/06_rag/README.md), ACL/citations и [протокол данных](../../docs/experiment-protocol.md).

Построить разрешённый corpus технической документации, настоящие embeddings,
постоянный Qdrant index и один явно выбранный local/external LLM provider.
Использовать существующие chunking/ranking/permissions/citations как контракты.
Не считать инструкции внутри документов или tool output доверенными командами.

Маршрут: [интуиция и разобранный пример](theory.md) →
[offline teacher trace](demo.py) → [явные runtime gates](runtime.md) →
[другая самостоятельная задача](exercise/README.md). Часть B проекта
[ссылается на эту lab](../../projects/document_intelligence_lab/part_b/README.md),
а не содержит ещё одну реализацию поиска.

Из корня репозитория, без установки пакетов, сети и серверов:

```powershell
.venv/Scripts/python.exe -m pytest labs/03_real_rag -q
.venv/Scripts/python.exe -m labs.03_real_rag.demo --output artifacts/r07-teacher-new
.venv-training/Scripts/python.exe -m labs.03_real_rag.dense random-mechanics
```

Выходная папка должна быть новой. Teacher trace хранит отдельные `retrieval.json`
и `answers.json`, точные bytes corpus/judgments и их SHA-256 в `manifest.json`.
`verify_trace` проверяет целостность bytes, не истинность ответов и не происхождение
чужого manifest. Привилегированный author trace содержит staff fixture; обычному
пользователю выдаётся только результат `answer_query` для доверенного actor access.
Полный trace не должен становиться пользовательским API или логом.

`demo.answer_query` явно выбирает локальный `extractive_generator`: он возвращает
выдержку, **не LLM**. Можно передать callable `(query, authorized_passages) -> Draft`;
адаптер обязан сам ограничить timeout/output и переводить outage в
`ProviderUnavailable`. Наличие допустимого citation ID проверяется механически;
смысловая поддержка ответа остаётся `REQUIRES_REVIEW`. Инструкции внутри passage
не исполняются. Синхронный wrapper не умеет прерывать произвольный зависший callable.

Optional [dense boundary](dense.py) проверяет существующий HF allowlist и загружает
только локальные safetensors. Его **экспериментальный CLS baseline НЕ является
рекомендованным mean pooling из MiniLM model card** и не наследует заявленное качество
этой модели. Он сохраняет две выдачи на фиксированных queries после явного запуска.
Random BERT показывает только `[B,T,H] -> [B,H]`; его числа не semantic benchmark.
Папка модели содержит ровно pinned обычные файлы; лишние loader inputs, ссылки
и вложенные каталоги отвергаются до загрузки, чтобы tokenizer bytes не выпадали
из inventory identity. Подробнее — [runtime gate](runtime.md).

Expected artifacts: snapshot+manifest, annotation queries/relevance labels,
ingestion/update/delete pipeline, lexical baseline, retrieval report и отдельный
answer report с citations/no-answer, latency/cost и ручной проверкой части ответов.

Done: зафиксированы Recall@k/MRR или nDCG по смыслу задачи; сравниваются lexical,
embeddings, chunking и metadata/ACL filtering; hybrid/reranking вводятся только
при измеренной пользе. Проверены удаление, обновление, отсутствие источника,
невозможность выдачи чужого документа. LLM-as-judge не единственная истина.
Любые внешние расходы требуют отдельного выбора пользователя.

Что уже проверяется offline: ACL до top-k; повторная сверка revision, digest и текста
перед генератором; update/delete/revoke; отсутствие основания; provider outage/recovery;
неизвестная ссылка; невалидные векторы; tamper; строгий тип schema_version.
Qdrant smoke проверен с настоящим `qdrant-client==1.19.1` в `.venv-rag`: public ACL
до top-1, revoke, delete, новая revision другого source, close/reopen и отдельный
process. [Разобранный запуск](runtime.md) начинается с `hand-snapshot`, не требует
model assets и сохраняет версии, SHA-256, ID/score и actual timing receipts.
Обычный pytest пропускает integration tests; явный gate `ROADMAP_RUN_QDRANT=1`
включает настоящий local disk client. [Фактические результаты](verification.md)
не доказывают pretrained семантику, LLM quality или production ANN свойства.
Новый exercise ID не добавляется: старые student TODO и progress сохранены.

## Полный dense → generator маршрут

[End-to-end evaluation](end_to_end/README.md) добавляет явный masked-mean pooling,
сравнение с прежним CLS, dev/holdout, отдельные retrieval/answer метрики и случаи
no-answer, ambiguity, stale и ACL. Новый ID `rag-end-to-end-evaluation` требует
самостоятельной реализации и реального локального evidence; старые CLS-отчёты
сохраняют свои подписи. Offline doubles не подтверждают качество генератора.
Порядок прохождения — [текущая карта](../../docs/learning-map.md).

## Модельная глубина retrieval

После lexical/dense/hybrid и retrieval evaluation выполните
[настоящий CrossEncoder reranker](neural_reranking/README.md), затем
[адаптацию embeddings](embedding_adaptation/README.md). Эти learner ID требуют
собственных данных/предсказаний и не закрываются illustrative score таблицей.
