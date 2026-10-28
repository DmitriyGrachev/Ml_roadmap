# Авторские R07 runs — 2026-10-11

<a id="minilm-local"></a>

## MiniLM: реальная модель, маленькое фиксированное сравнение

После явного разрешения пользователя получены ровно шесть файлов
`sentence-transformers/all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, total **91 567 205 bytes**.
Все size/SHA-256 совпали с [resources.json](../02_huggingface_models/resources.json),
проверена exact inventory. Dataset Bitext отсутствует. Других моделей не скачивали.

В `.venv-training` реально выполнен `dense encode-local` из [runtime.md](runtime.md):
CPU, eval/inference mode, batch≤8, max_length=128, размерность384, **CLS + L2**.
Это экспериментальная representation, не рекомендованный MiniLM mean pooling.
Модель не обучалась. `artifacts/r07-minilm-cls-20261011-v1/retrieval-comparison.json`
содержит public top-2, scores, per-query Recall@2/MRR; исходные judgments не менялись
после просмотра результатов. Corpus original synthetic, не персональные данные.

| Query | Lexical top-1 | CLS top-1 | Recall@2 lexical / CLS | RR lexical / CLS |
| --- | --- | --- | --- | --- |
| scanner settings | SCAN@1 | SCAN@1 | 1 / 1 | 1 / 1 |
| digitisation resolution | нет | SCAN@1 | 0 / 1 | 0 / 1 |
| reading room hours | HOURS@1 | HOURS@1 | 1 / 1 | 1 / 1 |
| volcano insurance | нет | APPENDIX@1 | null / null | null / null |
| cabinet code | нет | HOURS@1 | null / null | null / null |

По **трём answerable queries** mean Recall@2 и MRR: lexical 2/3, CLS 1.
По двум zero-positive judgments метрики null, а не выдуманные 0 или 1.
Это пять авторских примеров, не оценка generalization или победа MiniLM вообще.
Особенно важная ошибка: для отсутствующего ответа dense всё равно выдаёт соседей.
Top score `volcano insurance` ≈0.576952; порог answerability по этим пяти точкам
не выбирался. Private chunk исключён до top-k. Ответы LLM не создавались.

Snapshot manifest: `25c7d66fbe0cc42aef6badf7e2782211c3e82485ce7a18f0ef1acfaf2a10e374`.
Query/judgments bytes SHA: `2313e153619c954e380e9721928345b54f20f6832eef1b4b151775124597c898`.
Дополнительный actual query-vector record `query-evidence.json`:
`2cf5f89e81d95174fc5e1130943f0ff136a489c9a54cf10b8db738615690db87`;
seed17, Torch2.14.0+cpu, Transformers5.17.0, NumPy2.5.3. Записаны версии/PID/time,
memory NOT_MEASURED; не тренировочный seed-study и не latency benchmark.

Отдельно выполнен **pristine numeric Qdrant** run без старого mutation smoke:
`artifacts/r07-minilm-pristine-qdrant-20261011-v1/retrieval-receipt.json`,
SHA `f13614640377c12d890ad54b8e5019165c9591ca721f4f94c87c8372b12d7105`,
PID30112. Созданы четыре исходных points, `r07_pristine`, cosine384; metadata
содержит snapshot pin/full representation. Все пять реальных query vectors прошли
public filter **в Qdrant до limit=2**. Их ID/score совпали с NumPy CLS ranking
(числа atol/rtol1e-6). В отдельном process PID9896 проверены dimension/distance,
metadata, полный exact inventory/payload/vectors и повторены пять rankings.
Wall time0.0284431 /0.0147203s после import/preflight, не benchmark p50/p95.
`fresh-process-receipt.json` хранит вторую проверку. Ни classifier, ни generator
в этом опыте не вызывались. Выдачи в таблице выше подтверждены именно этим index.

С этой representation также выполнен старый Qdrant mechanisms-only smoke:
`artifacts/r07-minilm-cls-qdrant-20261011-v1`, PID31020; отдельный verify PID7068,
три persisted points, wall time0.5635882 /0.5124765s. Его update сохраняет старый
vector при новом тексте: **не использовать как корректный semantic index**.
Поэтому отдельно подготовлен новый B snapshot с заново embedded HOURS@2 (15:00),
SCAN access=staff и удалённым APPENDIX. Old/new HOURS cosine0.9908628759, vectors
различны; B manifest `9debc56f4b41b4a14629b49269025b0cd0275400a55fedf9f0e04cb5bd3e38a4`.
Старые relevance labels HOURS@1 для B не применялись. Согласованные индекс/recovery
и итоговые проверки — [runtime-продолжение](../../docs/local-runtime-continuation.md).

Технический PASS/измерение retrieval не означает quality генератора, пройденный
student check или выполненную часть B. Generator **NOT_RUN** и согласуется отдельно;
vLLM **DEFERRED_ENV**. Ни Torch GPU, ни serving, cloud, ANN/concurrency не проверялись.

## Предыдущий hand-authored Qdrant run

В Windows, Python 3.12.14, отдельная `.venv-rag`, `qdrant-client==1.19.1`.
Local disk `QdrantClient(path=...)`; без URL, сервера, Docker, model/data downloads,
FastEmbed или LLM. Корпус — synthetic teaching fixture с разрешением автора в
`fixtures/corpus.json`. Student TODO, progress и exercise IDs не изменялись.

Команды повторения с новыми путями находятся в [runtime.md](runtime.md).
Фактически использованы `artifacts/r07-hand-20261011` и
`artifacts/r07-qdrant-20261011`. Эти локальные артефакты исключены из Git; следующий
запуск должен выбрать новые пути. Snapshot manifest SHA-256:
`1990e806d5268b09598d4841edcb443c6292306d14e12ff982681ec50781a71e`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| sources.json | 829 | d989aeac3411e102ad9e4607b7a0be7099d84593f8a38957f901652a03c4bf7f |
| chunks.json | 1307 | c6b4e7995b1ed52626f13cbf542f14537dab6cf92cb6c16275fc287638aedcae |
| vectors.json | 157 | 84b780e2540c4a005167f2add7fe5745bc1f96fc31bc5d1e3231846f92ae4096 |
| manifest.json | 983 | 1990e806d5268b09598d4841edcb443c6292306d14e12ff982681ec50781a71e |
| mechanics-receipt.json | 3871 | be3deb2d9fd157ca884c1299f5aca9553e32abf7698091f0159b022d6a5233e0 |
| fresh-process-receipt.json | 980 | 739547d15f3fd2499741fd67fd64ef8e96e0abcdf2ef7c51873acbbd7330b13c |

Это receipt **hand-authored API geometry**, dimension=2, pooling=none, query=[1,0].
Actual observations:

| Этап | Наблюдение |
| --- | --- |
| Без ACL, top-1 | A-STAFF@1:p1, cosine 1.0 |
| Public ACL, top-1 | A-SCAN@1:p1, cosine 0.9938837289810181 |
| Public query после revoke SCAN | HOURS@1 score 0.0; APPENDIX@1 score -1.0 |
| Update HOURS | A-HOURS@1-qdrant-update:p1, новый text/digest/ID; старый ID удалён |
| Close/reopen и новый process | 3 exact persisted IDs; 2 public, 1 staff |

Point IDs (UUIDv5 от существующего chunk ID): удалённый SCAN
`69bbd301-d555-5dae-a8d8-b1dbac10a14e`; старый HOURS
`2ef03786-d95d-5a91-b34a-bb4b660ce22f`; новый HOURS
`ab239eca-0bea-519c-a858-a12d6b29f90f`; APPENDIX
`c3fe05bc-ddae-5e15-8303-47dcaaa42b48`; STAFF
`b33c4d50-64e6-553e-8833-82cf7cbdc63b`. Reopen сверил все payload и vectors,
dimension/distance, metadata representation identity и полный inventory, не только count.
Final inventory digest:
`c12f8a293dbf1aaa509f84fa26ff236afaa74872250e3c6ef316ac845bf755c3`.

Mutation/reopen process PID=19516; отдельный verification process PID=19736.
Измеренное wall time: mutation+reopen 0.6710309 s; отдельная verification 0.6377927 s
(включает lazy import/preflight). Это единичные измерения, не p50/p95 retrieval latency.
Code SHA-256 dense.py:
`4ac1ccb40440adff5860f15aa8268f2f220eff97db2fa3f0b071a5abe42c4e20`.

Явные actual tests проверяют отдельный process, отсутствие удалённых/stale ID,
отказ при намеренном возвращении этих ID, неправильной dimension и другой
representation inventory. Они используют настоящий package и temporary disk;
обычный pytest их пропускает даже при установленном package. Offline unit tests
дополнительно проверяют snapshot tamper и declared vector shape.

Проверки после изменений:

| Команда из корня | Фактический результат |
| --- | --- |
| `.venv-rag/Scripts/python.exe -m pytest labs/03_real_rag/test_qdrant_runtime.py -q` при `ROADMAP_RUN_QDRANT=1` | 6 passed, 4.35 s |
| `.venv/Scripts/python.exe -m pytest labs/03_real_rag tests/integration/test_markdown_links.py tests/integration/test_packet6_rag.py -q` | 67 passed, 8 skipped |
| `.venv/Scripts/python.exe -m ruff check labs/03_real_rag` | All checks passed |
| `.venv/Scripts/python.exe -m mypy -m labs.03_real_rag.dense -m labs.03_real_rag.test_dense -m labs.03_real_rag.test_qdrant_runtime` | no issues, 3 source files |
| `.venv/Scripts/python.exe -m pytest` | 1297 passed, 63 skipped, 1162 xfailed, 138.37 s |

В full pytest был один upstream Starlette `BlockingPortal` deprecation warning;
ошибок не было. Skips/xfails не превращались в выполненный student credit.

Pretrained embeddings/LLM quality: **NOT_RUN**. Hand geometry не доказывает Recall/MRR,
answerability или groundedness. В update переиспользован ручной vector; production
pipeline должен заново embed изменённый text и публиковать согласованную версию.
Crash recovery, server ANN, concurrency, transactional source/index publication,
стоимость и память не измерялись. Current-source/ACL recheck перед generator остаётся
обязательным по `answer_query`/`rag.assemble_context`; этот smoke generator не вызывает.
