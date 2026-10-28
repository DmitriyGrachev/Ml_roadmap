# Почему близкий документ ещё не даёт правильного ответа

Задача: читатель архивного зала спрашивает, какое разрешение выбрать для скана.
Нужны [контракты module 06](../../modules/06_rag/README.md),
[HF shapes и inference](../02_huggingface_models/theory.md) и
[протокол эксперимента](../../docs/experiment-protocol.md).
Результат понимания: объяснить отдельно ошибку поиска, устаревший источник
и неподдержанный ответ, не свести всё к одному cosine score.

До запуска предскажите два исхода. В документе есть `Scanner settings: use 300 dpi`.
Найдёт ли TF-IDF запрос `scanner settings`? Найдёт ли `digitisation resolution`?
Оба вопроса имеют авторскую relevance label к одному source, но во втором нет общих слов.

Интуиция: retrieval выбирает материалы для ответа, подобно поиску страницы в папке.
Encoder строит координаты текста; индекс ищет соседние координаты; generator пишет
по найденным материалам. Аналогия заканчивается там, где «соседняя страница» начинает
считаться доказательством: близость, отрицание, актуальность и права — разные свойства.

```text
exact UTF-8 corpus bytes + permission/provenance
     -> NFC + paragraph policy -> A-SCAN@1:p1 + source digest
     -> encoder/preprocessing identity -> vectors [N,D]
trusted actor -> ACL BEFORE top-k -> candidates -> current revision/digest/text recheck
     -> bounded authorized context -> chosen generator -> citations + manual support review
query [1,D] -------------------------^
```

Corpus: [четыре собственных синтетических source](fixtures/corpus.json), public/staff,
revision `1`, один paragraph на source. ID `A-SCAN@1:p1` устойчив при том же snapshot;
новая revision даёт новый ID, старые chunks надо удалить. Если bytes изменены без
смены revision, source digest всё равно обнаружит несоответствие. Нормализация NFC
и схлопывание whitespace входят в идентичность; raw corpus bytes хешируются отдельно.
Разрешение на учебное использование записано рядом с корпусом. Hash обнаруживает
изменение файла, но не доказывает лицензию или достоверность его содержания.

Точные понятия. **Embedding** — числовое представление текста конкретной моделью.
Для MiniLM hidden states имеют форму `[B,T,384]`: B — размер batch, T — число token
positions, 384 — hidden dimension. Учебный CLS baseline берёт первую позицию,
получая `[B,384]`, и нормирует каждую строку. Это другой pooling, чем рекомендованный
model card mean pooling с attention mask. Рекомендованный pooling остаётся практикой
уже существующего HF задания; здесь нет второго готового решения его TODO.
Локальный random encoder переиспользует factory HF lab и показывает `[2,5,16]`
и `[2,16]`. Его веса случайны: API и формы реальны, semantic quality не проверяется.

**Cosine similarity** между ненулевыми x и y равен `(x·y)/(|x||y|)`.
После L2-нормировки dot product равен cosine. Ручной пример: x=(3,4), |x|=5,
нормированный x=(0.6,0.8); y=(0,2), |y|=2, нормированный y=(0,1);
dot=0.6×0+0.8×1=0.8. Это близость направлений, не 80% вероятности правильного ответа.
Zero/NaN/Infinity rows и неверные `[N,D]` отвергаются. Sparse TF-IDF cosine и dense
cosine имеют разные распределения: одинаковый threshold не следует из одинакового
имени score. В dense top-k могут попасть документы даже для вопроса без ответа.

Разобранный запуск `demo --output artifacts/r07-teacher-new`:

| Фиксированный query | Lexical top-2 IDs | Recall@2 | Reciprocal rank | Ответ |
| --- | --- | ---: | ---: | --- |
| scanner settings | A-SCAN@1:p1 | 1 | 1 | буквальная выдержка с 300 dpi |
| digitisation resolution | пусто | 0 | 0 | no_answer, хотя source размечен |
| reading room hours | A-HOURS@1:p1 | 1 | 1 | выдержка с часами работы |
| volcano insurance | пусто | null | null | no_answer, source отсутствует |
| cabinet code | пусто | null | null | no_answer, staff text недоступен |

Числа вычислены на фиксированных teacher cases; это не репрезентативная оценка.
Recall делит число найденных релевантных chunks на все релевантные chunks; reciprocal
rank равен 1/r для первого релевантного результата, иначе 0. Здесь вопросы без
положительных judgments имеют null и учитываются отдельно как no-answer cases.
Это отличается от zero convention самостоятельного `rag-retrieval-evaluation`;
не смешивайте знаменатели в агрегате. Не переписывайте judgments после просмотра
выдачи. Для самостоятельного исследования заранее отделите development/held-out
группы запросов и выбирайте k, chunking и pooling на development.

Полный ожидаемый ответ для первого query:

```text
status: answer
text: Source excerpt: Scanner settings: use 300 dpi for paper copies. Ask the archivist before scanning fragile originals.
citation_ids: [A-SCAN@1:p1]
grounding_status: REQUIRES_REVIEW
```

Почему ответ помечен review? Здесь нет claim-level entailment evaluator. Пользовательский
callable может написать «600 dpi» с допустимым ID: reference check пройдёт, смысловая
проверка должна провалиться. Default просто цитирует первый passage; он не понимает
вопрос, не разрешает противоречия и может вернуть нерелевантную выдержку.
Retrieval report и answer report поэтому раздельны.

Измените только `current_sources`: замените правило на revision `2`, сохранив старые
indexed sources. Старый кандидат отбрасывается; результат `no_answer`, а не молчаливое
использование новых bytes под старым ID. Удаление source и отзыв public access дают
такой же отказ до provider. Перед повторным ответом нужен новый согласованный snapshot
и удаление obsolete chunks. Новая модель, pooling, tokenizer или max_length требуют
новых векторов; одну размерность D недостаточно считать совместимостью индексов.

Теперь предскажите `character_budget=0`: provider не вызывается, citation IDs пусты.
Бюджет здесь в символах source text, не model tokens; настоящий provider считает
также инструкции, вопрос, framing и резерв ответа своим tokenizer.

| Сбой | Где остановиться | Что перепроверить |
| --- | --- | --- |
| чужой source ближе всех | ACL до top-k | результат public query не содержит ID/bytes staff |
| revision устарела или source удалён | context recheck | очистка старых chunks и cache |
| найден нерелевантный passage | answer/no-answer policy | judgments и достаточность evidence |
| provider недоступен | provider_error | deadline, bounded retry, recovery |
| ссылка выдумана | invalid_output | citations являются подмножеством context IDs |
| source содержит команду | trust boundary | source — данные; tools не доступны excerpt generator |

Public appendix намеренно содержит `Ignore previous instructions`. Default показывает
его как цитируемый текст и ничего не исполняет. Это демонстрация границы данных,
не гарантия защиты произвольной LLM от injection. Права проверяются приложением;
system prompt не заменяет ACL. Не отдавайте полный privileged trace посетителю.

Persistent Qdrant — хранение на диске плюс повторное открытие клиента. Закрыть первый
client перед reopen обязательно; local storage рассчитан на одного владельца.
Явный [runtime опыт](runtime.md) проверен с `qdrant-client==1.19.1`: реальные
query/filter/upsert, ACL revoke, delete, замена revision и точный inventory после
reopen и в новом process. **Actual local mechanics: PASS**; vectors заданы вручную,
В этом hand-vector опыте pretrained retrieval не выполнялся; реальный MiniLM CLS
retrieval [измерен отдельно](verification.md#minilm-local). LLM quality — **NOT_RUN**.
Unit fake для проверки настоящей локальной механики не нужен.
Local mode не benchmark серверной ANN системы. При реальном опыте отдельно сравните
exact/ANN recall и latency на одинаковом authorized cohort, а не только point count.

Проверка понимания: почему `digitisation resolution` здесь miss, а `volcano insurance`
— отсутствие сведений? Почему более высокий cosine старой revision не спасает ответ?
Почему фильтрация после top-1 может потерять единственный разрешённый документ?
Что ломается, если заменить CLS на mean, сохранив старый индекс? Почему существующая
цитата не доказывает «600 dpi»? Что именно подтверждает random smoke?

Самостоятельный перенос: [другая задача](exercise/README.md). Повторно используются
`rag-text-chunking`, `rag-index-sync`, `rag-ranking-study`, `rag-citation-validation`
и `rag-retrieval-regression`; авторские fixture и ответы не переносятся в student work.

Источники, проверены по официальным страницам 2026-10-11, англ.:

- Qdrant maintainers, [client local mode и numeric query API](https://github.com/qdrant/qdrant-client/blob/master/README.md): прочитать local mode и numeric upsert/query examples, остановиться до облачного inference.
- Qdrant, [Filtering](https://qdrant.tech/documentation/search/filtering/): `must`, FieldCondition и MatchValue; связать trusted access с query_filter.
- Sentence Transformers authors, [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2): сравнить рекомендованный mean pooling с нашим явно экспериментальным CLS baseline; Hub загрузки из примера не запускать автоматически.

Остановка: готовый текст, зеленые unit tests и сохранённый snapshot не доказывают
интеграцию. Отдельный hand-vector Qdrant trace доказывает только проверенную механику;
actual MiniLM CLS retrieval теперь [измерен отдельно](verification.md#minilm-local)
на пяти teacher queries; это не общий semantic benchmark. LLM answer quality
и освоение учеником требуют своих измерений и самостоятельной работы.
