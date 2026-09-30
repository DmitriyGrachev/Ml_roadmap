# Компактное исследование ранжирования

Prerequisites: `rag-vector-search`, `rag-rank-fusion`, `rag-retrieval-evaluation`,
`rag-retrieval-regression`. Сначала завершите существующие функции
[ACL/vector search](../../03_lexical_dense_retrieval/exercises/vector_search/README.md),
[RRF](../../04_hybrid_reranking/exercises/reciprocal_rank_fusion/README.md),
[graded evaluation](../../06_rag_evaluation/exercises/retrieval_evaluation/README.md) и
[paired regression](../retrieval_regression/README.md).

Сравните **два самостоятельно выбранных offline метода** на одних held-out запросах.
Например, разные лексические представления или лексический метод и комбинация
рангов; это варианты, а не обязательные реализации. Метод и параметры выбираются
на train-запросах. Никаких downloads, pretrained embeddings или готового reranker.
Настоящие embeddings/reranker отложены до [реального RAG lab03](../../../../labs/03_real_rag/README.md);
deep LTR — OPTIONAL. Оценка retrieval не доказывает качество LLM-ответов.

## Что можно менять

Реализуйте `starter.py: run_study(output_dir: Path) -> Path`, добавляйте собственные
модули методов рядом. Fixtures, validators и tests — контракт; не редактируйте их.
`output_dir` должен отсутствовать: существующий каталог вызывает `FileExistsError`.
Все результаты — в новом каталоге; возвращается путь `manifest.json`.
Исходные учебные TODO метрик остаются в прежних упражнениях: здесь не копируйте
их алгоритмы и не подменяйте их готовой библиотекой ради зелёного зачёта.

## Данные и порядок действий

`fixtures/corpus.jsonl`, `queries.jsonl`, `judgments.json` содержат стабильные IDs,
текст, semantic groups и роли. Релевантность graded (0..3), разметка неполная:
отсутствующая оценка трактуется метрикой как ноль, но не доказывает нерелевантность.
Разделите **группы запросов**, чтобы парафразы одного намерения не попадали в обе
части. Train и test непусты, не пересекаются и вместе покрывают все query IDs.
Группы документов описывают тему; единица разделения — query group.

Авторизуйте список до cutoff: роли запроса должны пересекаться с `roles` документа.
Пустой список ролей не даёт доступа. Restricted лучший hit не должен вытеснять
доступный. Для RRF сначала авторизуйте каждый входной список и вызывайте прежний
`fuse_rankings`; при векторном поиске используйте прежний `vector_search` с ACL.
В остальных методах соблюдайте тот же ACL-контракт. Validator проверяет сохранённый
список до cutoff и итоговый run; фактическую последовательность ваших вычислений
проверяет человек по коду (артефакты не являются execution trace).

Вызовите настоящий `evaluate_retrieval` дважды и `compare_retrieval` для пары
методов. Можно использовать `evidence.recompute`: это композиция тех же функций,
без новой реализации метрик. Передайте graded judgments в первую функцию;
во вторую — `QueryJudgment` с grade > 0 и тот же k. Здесь запрещены дубликаты
даже после k: старые APIs различаются в обработке повторов, единый контракт
исследования намеренно строже. Для recall regression действуют старые пороги по
умолчанию; `passed=False` допустим как результат, это не провал исследования.

## Формат артефактов

Сохраните точные bytes трёх fixtures под теми же именами в output_dir, а также:

- `split.json`: `train_ids`, `test_ids` — списки query IDs.
- `outputs.json`: `run_id`, `dataset_sha256`, `split_sha256`; `methods` — объект
  ровно двух названных методов. Каждый содержит `rankings` (query ID → весь
  ранжированный список **до окончательного ACL/cutoff**, либо уже разрешённый
  полный список) и `runs` (query ID → авторизованный top-k). Оба объекта покрывают
  ровно test IDs. Неизвестные document IDs и дубликаты недопустимы.
- `outputs.json.metrics`: JSON-представление результата `evidence.recompute`:
  `methods` хранит `dataclasses.asdict(RetrievalEvaluation)` для каждого метода;
  `comparison` — `asdict(RegressionReport)`. JSON превращает tuples в arrays;
  сохраняйте точные числа без округления и замены float на bool/int.
- `implementation.txt`: снимок исполнявшегося кода ваших методов и настройки.
- `report.md`: постановка, выбор групп, два метода и параметры, таблица метрик,
  ошибки по запросам, ACL, оговорка о неполных judgments, вывод и ограничения.
- `manifest.json`: `schema_version: 1`, `exercise_id: "rag-ranking-study"`, непустой
  `run_id`, `dataset_sha256` (SHA-256 точных bytes corpus.jsonl), `split_sha256`
  (bytes split.json), `config: {"k": положительный int, ...}`, `review_status:
  "REQUIRES_REVIEW"`, `artifacts` — относительный путь → SHA-256 всех перечисленных
  файлов, кроме самого manifest. Порядок двух ключей `methods` определяет baseline
  и candidate; сохраняйте его, чтобы сравнение было осмысленным.

Validator проверяет bytes, identity, immutable judgments, IDs, группы, ACL и
**независимо пересчитывает** числа через существующие метрики из сохранённых runs.
Если prerequisites ещё TODO, чтение валидного результата поднимет
`NotImplementedError`; скрытого эталона метрик нет.

## Запуск и staged hints

Из корня репозитория в Windows/PyCharm с выбранной существующей `.venv`:

```powershell
uv run --no-sync python scripts/learn.py test rag-ranking-study
uv run --no-sync python scripts/learn.py check rag-ranking-study
uv run --no-sync python -m modules.06_rag.exercises.ranking_study.evidence C:/temp/my-ranking-run
```

1. Сначала выпишите роли и группы каждого query, выберите целые held-out группы.
2. Проверьте ограниченный лучший hit до top-k на двух документах.
3. Сохраните реальный run каждого метода; затем вызывайте обе старые метрики.
4. Перечитайте сохранённый каталог validator'ом; объясните хотя бы одну ошибку.

## Критерий и уровни свидетельств

Unit: ACL, IDs, split, integrity и композиция. Infrastructure tests используют
явные крошечные dependency spies с фиксированными результатами; они **не доказывают**
верность ваших метрик. Smoke: student test вызывает ваш run_study в свежем tmp и
наблюдает вызовы настоящих metrics, затем перечитывает artifacts. Evaluation:
фактические runs и graded/paired результаты на одинаковых held-out query IDs.
Review: выбор методов, отсутствие настройки по test, RRF/ACL путь при их выборе,
неполнота judgments и интерпретация требуют защиты человеком.

`test` допускает учебные xfail; `check` не принимает TODO/xfail/skip. Ни fingerprints,
ни совпадение метрик не доказывают, что сохранённые rankings получены вашим кодом:
привязка кода и результатов не аутентифицирует исполнение. Финальный статус
остаётся `REQUIRES_REVIEW`; автоматического утверждения о победителе нет.
