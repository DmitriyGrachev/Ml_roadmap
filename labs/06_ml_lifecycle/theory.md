# Lifecycle: какие байты вернуть и что на самом деле ухудшилось

## Задача и prerequisites

Сервис отвечает, но изменилось распределение входов. Последний run показывает
высокую accuracy. Можно ли сразу переобучить модель и переключить alias?
После урока нужно назвать недостающее свидетельство, выбрать совместимый набор
для восстановления и проверить фактический ответ после restart.
Нужны [split/fit/evaluation](../../modules/04_machine_learning/06_reproducibility/theory.md),
[release evaluation](../../modules/08_production_ai/02_releases_evaluation/theory.md),
[observability](../../modules/08_production_ai/03_observability/theory.md)
и [rollout/incidents](../../modules/08_production_ai/06_rollout_incidents/theory.md).
Там уже разобраны общие release gates; здесь только конкретный teacher lifecycle.

## От строки до версии данных

Data release — зафиксированный результат подготовки, не меняющийся CSV по пути
`latest.csv`. Row identity показывает, откуда пришла строка; content hash — какие
байты у текста; group identity удерживает связанные paraphrases вместе. Эти
три вещи отвечают на разные вопросы. Annotation guide задаёт смысл label,
rubric/schema версии и маршрут спорных записей на review. Новое правило разметки
может изменить задачу даже при неизменном тексте.

```text
Строка + provenance + rubric
            |
       batch ≤ B строк
            |
dataset bytes + schema + rejects/review
            |
 fixed group-aware split identity
            |
 train-only preprocessing + model
            |
 release digest + выбор человека
```

В [data-release-study](../../modules/03_data_foundations/exercises/data_release/README.md)
уже есть точный контракт source/line/row_id, проверки provenance bytes,
accepted/rejected/review, deterministic split, запрет перезаписи и ограниченные
buffers. Не переписывайте его внутри этой lab. Для backfill заранее задайте
source partition/revision и stable row IDs; новый batch не означает новый business
entity. Replay в **другой** новый каталог должен дать те же data/split bytes.
После сбоя нельзя append повторно и надеяться, что дублей нет. Нужен завершённый
manifest либо незавершённый результат, который ещё нельзя потреблять.

Прогноз: N растёт с 200 до 2000 при B=32. Осталась ли вся память ограниченной?
Нет: предел batch не ограничивает глобальный dedup/label index. Укажите единицы
и предел каждого state, disk index/cache или явный fail при исчерпании. Измеряйте
реальный buffer boundary, Python allocations и/или RSS с объяснением различий.
Существующие [lazy stream](../../modules/01_python_core/07_iterators_generators/exercises/stream_transactions/README.md)
и [paged stream](../../modules/01_python_core/exercises/paged_stream/README.md)
остаются prerequisites. Этот tiny demo не измеряет память и не выдаёт small fixture
за доказательство memory-aware production pipeline.

## Run, storage, registry и release

Run — запись попытки и её протокола. Artifact storage хранит bytes, registry
даёт именованную версию и aliases, release manifest связывает совместимые части.
Здоровая SQLite база с metadata не доказывает, что model bytes ещё доступны.

```text
MLflow run: params + metrics + IDs → artifact bytes + flavor
                                             |
                             registry version / alias

release manifest digest связывает:
  ├─ model + preprocessing
  ├─ data + split + sources
  ├─ code + config + versions
  └─ optional corpus / index / embedding bundle
                 |
         выбор человека (human gate)
                 |
       NEW restore → replay → readiness
```

Здесь `releases.write_release_new` копирует только проверенный inventory из A1,
а `verify_release` сверяет complete bundle и повторно вычисленную identity.
Копия содержит model bytes, data/split/sources, predictions, metrics, selection,
measurement и manifest. Preprocessing встроен в rules contract или fitted sklearn
Pipeline, а его контракт и порядок labels привязаны manifest. Code/source hash
из bundle фиксирует исходники обучения; отдельный lifecycle source hash фиксирует
writer. Git revision при dirty worktree недостаточен. Hash — integrity относительно
доверенного внешнего значения, не подпись издателя и не защита от concurrent writes.
Рабочие каталоги и operator config должны быть защищены от замены.

Прогноз: изменить `identity.preprocessing.version` и пересчитать release digest.
Проверка всё равно отвергнет пакет: identity расходится с actual bundle. Если
переписать все bytes и доверенный внешний config, integrity boundary уже потерян.
Если удалить `model.json`, recovery остановится до создания destination.
Если destination уже существует, повтор остановится, сохранив прежние bytes.

В [demo](demo.py) A — две rules с fallback circle, B — реальный fitted TF-IDF.
Для `triangle` свежий A отвечает `circle`, B отвечает `triangle`, неверный ожидаемый
digest B запрещает startup, свежий восстановленный A снова отвечает `circle`.
Это различие реально вычислено, а не подставлено из имени версии. Затем A
копируется в другой release/recovery каталог и ещё раз проходит actual service
lifespan, readiness и probe. Каждый loader replay сверяет saved test predictions.
Мы не утверждаем, что A лучше: rollback проверяет возврат выбранного поведения,
а human quality gate — отдельное решение на подходящей выборке.

```text
A / circle → B / triangle → неверный expected digest: startup отклонён
                                              |
                                  новый lifespan A / circle
                                              |
                                  NEW recovered-A / circle
```

Изменение одной строки `expected_release_sha256="0" * 64` у restore вызывает
ошибку, а не fallback. Не вычисляйте expected digest из файла, который принесли
после инцидента: получите ранее сохранённое значение из operator decision record.
`index=null` означает classification-only. Для RAG откатываются согласованные
corpus/index revision, vector dimension, embedding/tokenizer и ACL contract;
откат одного classifier filename этого не проверяет. Совместимый RAG release
rollback не проверяется этим старым classification-only demo. Теперь отдельный
[coupled local пример](coupled-recovery.md) восстановил согласованные classifier,
MiniLM bytes, corpus/representation и полный Qdrant inventory в новых папках.
Это не production deployment/atomic switch и не откат текущей authorization policy.
[Local Qdrant mechanics](../03_real_rag/verification.md) на ручных vectors остаются
отдельным ранним опытом, не доказательством semantic quality.

## Drift, labels и время

Data drift — изменение распределения X. Concept drift — изменение отношения
между X и целевой Y. Delayed labels — пока неизвестная Y; задержка не доказывает
ни стабильность, ни падение качества. Доля предсказаний, длина текста, OOV и
latency — полезные proxy для расследования, но не ground truth accuracy.

В demo все тексты и label relation **сконструированы автором**, реальные только
вычисленные model outputs и `perf_counter` timings. Никаких выводов о населении
или production detector из четырёх строк не следует. A используется во всех
windows, поэтому model identity не смешивается с изменением окна.

| Порядок window | Triangle token / все X | Доступно labels | Actual correct / labeled | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| reference | 0/4 | 4/4 | 4/4 | 1.00 |
| input-shift | 2/4 | 4/4 | 2/4 | 0.50 |
| label-relation-change | 0/4 | 4/4 | 0/4 | 0.00 |
| labels-delayed | 2/4 | 0/4 | неизвестно | null |

Прогноз: если оставить одну известную label из двух requests и ошибиться на ней,
accuracy равна 0/1, а не 1/2; label coverage — 1/2. Нельзя считать unlabeled успехом,
ошибкой или делить correct на все обращения. Для каждой window сохранены count,
labeled_count, predicted proportions с **общим count** в знаменателе, actual per-row
predictions/truth/times. Triangle fraction измеряет одну явную feature, а не полное
распределение X. При label-relation-change feature fraction и predictions прежние,
а качество другое: этот constructed контрпример опровергает «proxy доказывает accuracy».
В реальности такой результат требует проверки annotation/rubric версии и качества
labels; toy label swap сам по себе не устанавливает настоящую причину инцидента.

SVG строится из сохранённых измерений: ось fraction/accuracy от 0 до 1, time в ms,
порядок windows сверху вниз, n и label support рядом. Отсутствующая quality не
рисуется как ноль. Direct-call latency включает нормализацию/модель; ASGI timings
из reused recovery записаны отдельно. Оба режима warm after loader replay;
16 последовательных tiny requests не оценивают throughput, p99 или нагрузку.
Memory unknown, native/process peak не измерен. Raw production text в telemetry
по умолчанию не нужен: фиксируйте минимальные IDs, версии, длительность, outcome,
bounded aggregates и разрешённые delayed-label joins с retention/privacy policy.

## Human gate и действие

Перед promotion фиксируют data/split/rubric, cohort/slices и quality/resource budgets,
restore/parity, владельца решения и сохранённый previous digest. Shadow получает
копию разрешённого traffic без воздействия на ответ; canary обслуживает ограниченную
долю с заранее названными stop/rollback условиями. Эти deployment режимы здесь
описаны, но не запускались. Alert открывает расследование: input/schema change,
missing artifacts, runtime errors, preprocessing mismatch, delayed/corrupted labels
или изменённая задача требуют разных действий. Retrain не исправит сломанный mount.
Human принимает hold, ограничение traffic, rollback либо новый эксперимент.

После инцидента [runbook](runbooks/recovery.md) требует actual selected bundle,
replay и readiness, проверку metric denominators, timeline и повторного restart.
CI unit smoke — не hosted CI/deployment proof. Нет отдельной полной платформы.

Проверьте понимание:

1. Почему run ID не заменяет release digest?
2. Что останется известно, если database жива, а artifact root удалён?
3. Какие два независимых знаменателя нужны при partial labels?
4. Может ли concept relation измениться при прежней input feature histogram?
5. Почему исправленный alias ещё не доказывает восстановление preprocessing/index?
6. Когда drift alert требует проверки разметки, а не retraining?
7. Как batch B и dedup index ограничивают разные ресурсы backfill?

Самостоятельно выполните [другую вариацию](exercise/README.md). Старые
`production-release-gate`, `production-artifact-manifest` и `data-release-study`
сохраняют собственные TODO и проверки; teacher не даёт им зачёт.

Источники: точные локальные prerequisites выше; MLflow
[registry workflow](https://mlflow.org/docs/latest/ml/model-registry/workflow/)
и [client API](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.client.html),
англ., для [recipe](runbooks/registry.md); проверены через official docs 2026-10-11,
останавливайтесь на registration/aliases, не разворачивайте remote platform.
Документация сама по себе не доказывает работу runtime. Настоящий local MLflow
[проверен отдельно](../../docs/local-runtime-continuation.md); полный совместимый
service/index lifecycle этим опытом не подтверждён.
