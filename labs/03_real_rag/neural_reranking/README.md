# Нейронный reranking: кандидаты, порядок и стоимость

**ID:** `rag-neural-reranking`. **Optional group:** `ranking`.
Предварительно: dense retrieval, cosine similarity, train/dev/holdout и Python callbacks.
Результат: собственный reranker поверх реального локального `CrossEncoder`, независимый
набор запросов и проверяемое сравнение исходного и нового порядка. Авторские random
модели проверяют API; они не доказывают качество и не дают learner credit.

## Почему второй этап нужен после retrieval

Bi-encoder независимо кодирует запрос и документ: `u=f(q)`, `v=f(d)`, `s=u·v` после
L2-нормировки. Документы можно закодировать заранее, затем искать близкие векторы.
Cross-encoder совместно читает пару `[query, document]` и возвращает score. Взаимодействие
токенов позволяет учитывать детали пары, но повторный forward нужен для каждого кандидата.
Снимок должен иметь один выход; здесь используется raw logit, а не калиброванная вероятность.

Пусть retriever вернул C документов, из них R релевантны, а во всём корпусе есть G
релевантных документов. **Candidate recall = R/G**. Перестановка C не изменяет этот потолок.
Отсутствующий документ reranker восстановить не может. Если он плохо оценил два имеющихся
документа — это ошибка порядка; если нужного документа нет в C — сначала чините retrieval.
Доступ и актуальность фильтруются до передачи кандидатов модели. Gold qrels используются
только оценкой после ranking и никогда не передаются scorer.

## Контракты самостоятельной реализации

В `starter.py` оставлены прямые `NotImplementedError`.

| Функция | Вход | Обязательное поведение |
| --- | --- | --- |
| `rerank(query, candidates, scorer, k)` | непустой query; кандидаты `{id, text}`; callable над списком пар | Ровно один вызов scorer для непустого списка; у пустого списка вызов отсутствует; один конечный scalar score на кандидата |
| результат `rerank` | список `{id, text, score}` | До `k` исходных документов, без новых ID/подмены текста, без изменения входа; сортировка `(-score, id)` |
| `ranking_metrics(rankings, qrels, k)` | полный порядок всех кандидатов по каждому query ID; grades 0..4 | Отдельный результат каждого запроса: `candidate_recall`, `mrr_at_k`, `ndcg_at_k` |

`k` — положительный `int`, bool запрещён. Повторные document IDs, несовпадение query IDs
между rankings/qrels, отрицательные/нецелые grades, NaN/Inf и несогласованная длина scores
дают `ValueError`. Неизвестные qrels документам в конкретном candidate pool допустимы:
именно так видны провалы retrieval. Grade 0 означает нерелевантный документ. Непомеченный
документ имеет gain 0; это допущение неполной разметки нужно обсудить в анализе.

`rankings` содержит **всех** кандидатов, не обрезанный top-k. Candidate recall использует
весь список, MRR/nDCG — первые k. Для отдельного recall@k нужен другой ключ; здесь его нет.
Пустой список при положительных qrels даёт три нуля. Если положительных qrels нет, все
три значения `None`; такие запросы исключаются из среднего, их число показывается отдельно.
Это не «идеальный» score за правильно найденное отсутствие ответа.

## Полностью разобранный пример

Запрос `q1`: gold `a:2, b:1, c:1`; retrieved/reranked список `[b, x, a]`, k=3.
Документ c отсутствует, x не размечен и получает 0.

| Ранг i | ID | Grade | Gain `2^grade−1` | Вклад в DCG `gain/log2(i+1)` |
| --- | --- | --- | --- | --- |
| 1 | b | 1 | 1 | 1 |
| 2 | x | 0 | 0 | 0 |
| 3 | a | 2 | 3 | 1.5 |

Candidate recall = 2/3. Первый релевантный документ на позиции 1, значит MRR@3=1.
DCG@3=2.5. Идеальный порядок **по всем qrels**, включая c: `[a,b,c]`.
IDCG@3=`3 + 1/log2(3) + 1/2 ≈ 4.13093`, nDCG@3≈0.60519.
Нельзя строить IDCG только из найденных документов: это скроет отсутствие c.
При k=1 candidate recall всё ещё 2/3, а nDCG@1=1/3. Если релевантный документ находится
только на второй позиции и k=1, MRR@1=0, даже если candidate recall положителен.

## Настоящий локальный запуск

Зависимости устанавливаются отдельно: `uv sync --group ranking`. Обычный import/pytest
не скачивает веса и не запускает training. Проверенная поверхность API: sentence-transformers
6.2.0, transformers 5.17.0, torch 2.14 CPU. `runtime.local_scorer` вызывает настоящий
`CrossEncoder(..., local_files_only=True, trust_remote_code=False, device="cpu")`.
Снимок — существующий каталог с `config.json`, tokenizer и safetensors; запрещены symlinks
и pickle weights. Максимум 1000 файлов/2 GB. Большие модели выходят за бюджет этой лабораторной.

При необходимости загрузка является **отдельной сознательной network-командой**, здесь
она не выполнялась. Сначала задайте проверенные вами model ID, immutable revision и лицензию:

```bash
hf download "$MODEL_ID" --revision "$MODEL_REVISION" --local-dir .model-cache/reranker
```

В `provenance.json`: `{"kind":"pretrained","model_id":"...","revision":"полный commit","license":"..."}`.
Самодекларация не подтверждает происхождение модели; examiner проверяет manifest и повторяет запуск.
В независимом `cases.json` задайте:

```json
{
  "corpus": [{"id":"a","text":"Документ A"},{"id":"b","text":"Документ B"}],
  "queries": [
    {"query_id":"dev-1","query":"Вопрос разработки?","split":"dev","candidate_ids":["b","a"]},
    {"query_id":"hold-1","query":"Другой вопрос?","split":"holdout","candidate_ids":["b"]}
  ],
  "qrels": {"dev-1":{"a":2},"hold-1":{"a":1}}
}
```

Это схема, не достаточный независимый benchmark. Настоящие candidates должны происходить
из вашего retriever, а не сортироваться по qrels. Зафиксируйте его конфигурацию и снимок
корпуса в review. Query IDs и нормализованные тексты уникальны; dev/holdout обязательны.
Лимиты: 5000 документов, 1000 запросов, 200 кандидатов на запрос. Настройку размера candidate
pool, k и модели делайте на dev; holdout открывайте после фиксации выбора.

Дополнительно весь `report.json` ограничен **10 000 000 UTF-8 bytes**, а не символов.
До загрузки модели проверяется общий бюджет данных, повторённого текста кандидатов, scores,
метрик и известных metadata с резервом 128 KiB. Поэтому перечисленные лимиты строк/документов
не разрешают превышать общий бюджет. Финальная сериализация повторно ограничена тем же числом
байтов; при переполнении успешный report не записывается.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
uv run --group ranking python -m labs.03_real_rag.neural_reranking.runtime \
  --run-local --model-dir .model-cache/reranker --data cases.json \
  --provenance provenance.json --k 5 --output artifacts/rag-neural-reranking/learner
```

Каталог output должен быть новым. Runner вызывает именно learner `rerank/ranking_metrics`,
сохраняет полный порядок candidates, baseline metrics, scores, wall time, source SHA256,
hashes локальных файлов и входные данные в `report.json`. Ошибка/незаполненный TODO прерывает
запуск; успешного report нет. Не запускайте random author snapshot с фиктивной provenance.

Рядом создайте `review.json`: `status="REQUIRES_REVIEW"` и содержательные строки минимум
40 символов в полях `candidate_ceiling`, `failure_analysis`, `cost`, `transfer`,
`provenance_review`. Объясните собственный домен, разметку, dev-выбор и перенос на новый корпус.
Укажите число пар, batch, токены/обрезание, CPU и scope времени. Измеренное время исключает
загрузку модели; это последовательный небольшой эксперимент, не оценка throughput сервиса.

```bash
ROADMAP_RUN_RANKING=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 \
uv run --group ranking pytest -q labs/03_real_rag/neural_reranking/test_author_smoke.py

ROADMAP_RUN_RANKING=1 ROADMAP_RERANKING_SUBMISSION=artifacts/rag-neural-reranking/learner \
uv run --group ranking pytest -q labs/03_real_rag/neural_reranking/test_starter.py \
  labs/03_real_rag/neural_reranking/test_library.py \
  labs/03_real_rag/neural_reranking/test_submission.py
```

Author smoke создаёт random one-layer BERT с локальным vocab, реально вызывает
`CrossEncoder.predict` и `rank`, сопоставляет scores/indices. Он не является готовой
реализацией learner функций. Skip, xfail и smoke не дают строгого зачёта. Parser evidence
проверяет согласованность, но не аутентифицирует запуск; финальный gate — независимый rerun
и человеческая проверка нового домена/авторства.

## Ошибки, цена и перенос

Candidate recall=0: увеличьте/исправьте retriever, chunking или ACL. MRR хороший, nDCG плохой:
первый частично полезный документ найден, но лучший ответ ниже. Стабильный tie-break по ID
обеспечивает воспроизводимость; score двух разных моделей нельзя сравнивать как вероятности.
Обрезание длинного документа может удалить важный конец; отрицания, числовые параметры и
соседние версии инструкции требуют отдельных cases. Увеличение C добавляет pair-forward
и latency; измеряйте цену вместе с gain на dev, затем один раз на holdout.

Ranking оценивает порядок документов. Даже идеальный ranking не проверяет верность,
цитирование и допустимость ответа генератора: для этого сохраните отдельный answer evaluation
из end-to-end RAG. Перенос принят, если новый домен имеет независимые qrels/candidates,
разобраны хотя бы ошибки отсутствия и ошибки порядка, показаны denominators/no-relevant cases,
стоимость и ограничения, а examiner может воспроизвести локальные веса и код.

API reference: [CrossEncoder](https://sbert.net/docs/package_reference/cross_encoder/cross_encoder.html).
