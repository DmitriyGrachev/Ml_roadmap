# Адаптация embeddings на доменных тройках

**ID:** `rag-embedding-adaptation`. **Optional group:** `ranking`.
Prerequisites: dense retrieval, masked mean pooling, cosine, gradients/optimizer и раздельные
train/dev/holdout. Цель — самостоятельно собрать supervision, обучить настоящий локальный
`SentenceTransformer`, сохранить checkpoint и сравнить baseline/adapted на одних heldout queries.
Никакого обязательного порога улучшения нет. Честно полученное ухудшение с анализом допустимо.

## Что меняет адаптация

Bi-encoder отображает запрос и документ независимо в общее векторное пространство, поэтому
документы индексируются заранее. Cross-encoder совместно читает пару и дороже при повторном
ранжировании. Адаптация bi-encoder меняет саму геометрию retrieval; после training нужно
**переиндексировать весь корпус**. Сравнивать новые queries со старыми embeddings нельзя.
Близость темы ещё не означает пригодность ответа: две инструкции одной модели устройства
могут описывать противоположные настройки или разные версии политики.

Данные: query q, проверенный positive p, difficult but irrelevant negative n. Hard negative
нужно взять из реального поиска и проверить человеком. Высокая similarity делает пример
полезным, но одновременно повышает риск false negative: другой верный ответ, дубликат,
парафраз или документ с нужным ответом в обрезанной части. Не превращайте автоматически
все неразмеченные документы в доказанно отрицательные.

## Objective и выравнивание батча

Здесь используется реальный `sentence_transformers.sentence_transformer.losses.TripletLoss`
с cosine distance и margin 0.2:

`d(u,v)=1−cos(u,v)`;
`L_i=max(0, d(q_i,p_i)−d(q_i,n_i)+0.2)`; loss — среднее по строкам батча.
Например, cos(q,p)=0.7, cos(q,n)=0.65: `L=max(0,0.3−0.35+0.2)=0.15`.
Нулевой loss допустим, если margin уже достигнут; это не доказательство хорошего holdout.

Токенизируйте три списка отдельно, **с одинаковым порядком строк**. Вызов objective получает
`[query_features, positive_features, negative_features]`, padding обрабатывает Transformer/
Pooling attention mask. Labels у этой loss не несут target-классов; нужен совместимый tensor
длины batch. Затем backward, проверка finite gradients и optimizer.step. Seed задаётся до
shuffle/optimization; dropout/CPU settings записываются. В learner API максимум 20 шагов,
batch не более 8; это учебный бюджет, не промышленная стратегия обучения.

Эта triplet loss не использует остальные positives как in-batch negatives. В
`MultipleNegativesRankingLoss` positive другой строки обычно становится negative для текущего
query. Тогда одинаковые/эквивалентные positives, связанные query families и несколько верных
ответов внутри батча дают неверный supervision. Потребуется sampler без таких пересечений,
политика фильтрации и подходящая loss. Сам факт вызова популярной loss качество не гарантирует.

## Самостоятельные границы

| Функция в `starter.py` | Контракт |
| --- | --- |
| `make_triples(queries, corpus)` | По исходному порядку query/positive/negative создаёт строки с `query_id, query, positive_id, positive, negative_id, negative, family, split`; неизвестные ID отклоняет |
| dedup/filter | Дубликаты positive IDs/нормализованного positive text и одинаковые triples исключаются; все известные positives и их text aliases исключаются из negatives |
| `split_queries(queries)` | Сохраняет порядок и исходные строки в `train/dev/holdout`; query IDs уникальны, нормализованный query text уникален; одна normalized family не пересекает splits |
| `fit_encoder(model, triples, steps=..., seed=...)` | Обучает и возвращает тот же настоящий SentenceTransformer; cosine TripletLoss margin 0.2, CPU, steps 1..20, batch≤8, конечные gradients и изменение параметров |

Все функции остаются прямыми TODO. `fit_encoder` в конце оставляет gradients последнего
шага доступными проверке; checkpoint пишет runner. Не импортируйте author smoke как learner
решение. Простое изменение весов ещё не доказывает правильность loss: library test проверяет
механизм, разметка, alignment и objective дополнительно проверяются review/кодом.

## Изоляция данных

Family — реальная группа связанных документов/версий/шаблонов, а не случайная метка на query.
В train/dev/holdout не должны разделяться парафразы одного вопроса и документы одной family.
Входная schema содержит family у query; автор данных обязан построить её из связанного корпуса.
Автоматический checker проверяет переданные метки и normalized texts, но не распознаёт
семантическое родство или ложные family labels. Проверьте, что hard negatives train также не
занесли heldout family в обучение; эту семантику человек подтверждает в review.

Train используется только optimization. Выбор negative mining, checkpoint, steps, margin,
batch и k — на dev. Holdout оценивается после фиксации выбора. `runtime` не подбирает
гиперпараметры; параметры фиксированы до baseline/adapted heldout loops. Не выбирайте лучший
из нескольких запусков по holdout. Корпус retrieval одинаков в обеих ветвях; encode корпуса
выполняется заново каждым model, queries и positives сохраняют query identity.

## Локальный pretrained эксперимент и артефакты

`uv sync --group ranking` — отдельная установка. Все imports без загрузки весов; обычный
pytest не обучает. Реальные API проверены на sentence-transformers 6.2.0, transformers 5.17.0,
torch 2.14 CPU. Runner требует существующий SentenceTransformer snapshot с `modules.json`,
локальными safetensors/tokenizer/config, `local_files_only=True`, `trust_remote_code=False`.
Symlinks/pickle weights запрещены; snapshot ограничен 1000 файлами/2 GB.
Если требуется получить pretrained snapshot, это отдельная network-команда, не выполнявшаяся
в авторской проверке:

```bash
hf download "$MODEL_ID" --revision "$MODEL_REVISION" --local-dir .model-cache/domain-encoder
```

Нужны проверенные вами model ID, immutable revision и лицензия. `provenance.json` содержит
`kind="pretrained", model_id, revision, license`. Это декларация, её проверяет examiner.
Random author model не становится pretrained от смены строки evidence_kind.

Схема самостоятельного `data.json`:

```json
{
  "corpus": [{"id":"p","text":"Верная инструкция"},{"id":"n","text":"Похожая, но неверная инструкция"}],
  "queries": [
    {"query_id":"q1","query":"Вопрос train","family":"family-train","split":"train","positive_ids":["p"],"hard_negative_ids":["n"]}
  ]
}
```

Фрагмент показывает **только форму**, он не пройдёт проверку полноты. Требуются независимые
train/dev/holdout families и настоящие примеры из вашего домена; не копируйте эти два документа
во все splits. Лимиты: 5000 документов, 1000 queries, не более 100 IDs каждого вида у query,
10000 итоговых train triples. Каждому train query нужна хотя бы одна допустимая тройка.

Общий `report.json` ограничен **10 000 000 UTF-8 bytes**, включая данные, обе retrieval-ветви
и metadata. До загрузки модели проверяется combined budget с резервом 128 KiB для ещё
неизвестных metadata checkpoint; проверка входа консервативно учитывает максимальный k=100.
Число строк и длина текста — дополнительные лимиты, не разрешение превысить общий размер.
Перед записью финальные сериализованные bytes повторно проверяются; overflow прерывает
запуск без успешного report.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
uv run --group ranking python -m labs.03_real_rag.embedding_adaptation.runtime \
  --run-local --model-dir .model-cache/domain-encoder --data data.json \
  --provenance provenance.json --steps 2 --seed 7 --k 5 \
  --output artifacts/rag-embedding-adaptation/learner
```

Runner передаёт learner optimization **только train triples**, ограничивает sequence length
128, CPU threads=1, сохраняет `adapted/`, проверяет истинное изменение весов и checkpoint reload.
`report.json` включает data, source SHA256, baseline/adapted snapshot hashes и weight hashes,
одинаковые heldout query IDs, retrieval IDs/scores, recall@k/MRR@k, dev результаты и времена.
При failure нет успешного report. Output должен быть новым каталогом; повторный запуск требует
нового пути. `artifacts/` игнорируется git. Модель не обучается по import или обычному pytest.

Добавьте `review.json`: `status="REQUIRES_REVIEW"`; содержательные строки минимум 40 символов
в `hypothesis`, `dev_selection`, `false_negatives`, `failures`, `transfer`, `provenance_review`.
Запишите sampler, проверку families/false negatives, точный optimizer/LR/batch, dev-решение,
случаи улучшения и ухудшения. Отдельно объясните усечение текста и scope CPU wall time.
Parser проверяет согласованность и файлы checkpoint, но не доказывает честность происхождения
данных или запуска. Examiner повторяет trusted learner код и проверяет новый домен вручную.

```bash
ROADMAP_RUN_RANKING=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 \
uv run --group ranking pytest -q labs/03_real_rag/embedding_adaptation/test_author_smoke.py

ROADMAP_RUN_RANKING=1 ROADMAP_ADAPTATION_SUBMISSION=artifacts/rag-embedding-adaptation/learner \
uv run --group ranking pytest -q labs/03_real_rag/embedding_adaptation/test_starter.py \
  labs/03_real_rag/embedding_adaptation/test_library.py \
  labs/03_real_rag/embedding_adaptation/test_submission.py
```

Author smoke: локальный random one-layer BERT + **настоящий** mean Pooling; две фиксированные
тройки, два AdamW updates, cosine TripletLoss, ненулевые gradients/parameter change, сохранение
и reload. Это проверка механизма без pretrained retrieval claim. Skip/xfail/author output не
засчитываются как learner completion. Строгий catalog включает только learner tests.

## Ошибки и критерии переноса

Слишком похожие positives/negatives могут быть ошибкой разметки; loss будет учить неверное
различие. Случайный negative часто слишком лёгкий, поэтому loss быстро нулевой без реального
прогресса. Train loss вниз при holdout retrieval вниз — возможны переобучение, загрязнение
families, mismatch query/document prefixes или слишком узкий домен. Нельзя сравнивать векторы
разной версии модели. Recall улучшился при MRR хуже — найдено больше полезных документов,
но они ниже; проверьте трудные первые позиции и reranker.

Качество retrieval отделено от качества ответа: генератор всё ещё может исказить верный
контекст. Для ответа нужны отдельные проверки factuality/citations/abstention из end-to-end
лабораторной. Перенос принят при воспроизводимых исходных/новых весах, раздельных families,
независимой разметке, одинаковом heldout наборе, честном учёте стоимости reindexing/training
и содержательном разборе ошибок. Положительная дельта сама по себе недостаточна.

API references: [SentenceTransformer](https://sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html),
[losses](https://sbert.net/docs/package_reference/sentence_transformer/losses.html).
