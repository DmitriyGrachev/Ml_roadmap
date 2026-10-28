# Часть B: поиск по документам и ответы с основаниями

Реализация и теория находятся в [Real RAG lab](../../../labs/03_real_rag/README.md).
Часть B использует её corpus/index/provider contracts и не дублирует retrieval code.
RAG corpus identity независима от classification dataset/split identity части A.
Одна метрика classifier не оценивает поиск или support ответа.

Практика: выполните [самостоятельную вариацию lab](../../../labs/03_real_rag/exercise/README.md)
на своих разрешённых документах. Свяжите corpus/embedding/index manifest digest
с выбранным generator/config и release. Сервис получает доверенный actor access,
применяет ACL до top-k и сверяет текущую revision перед передачей context.
Не передавайте protected text классификатору/генератору только потому, что ветка
workflow уже выбрана. Routing не заменяет авторизацию.

На защите покажите lexical и real encoder выдачу на заранее размеченных queries,
объясните одну потерю релевантного источника и отдельно неподдержанное утверждение.
Проверьте update/delete/restart/отзыв доступа, no-answer и provider outage/recovery.
Документы и tool output остаются недоверенными данными. Отдельно предъявите
retrieval report, answer review и фактические timings/cost.

Состояние: author offline mechanisms доступны; настоящий local Qdrant с
ACL/update/delete/restart и отдельный actual MiniLM CLS retrieval на пяти queries
[проверены в lab](../../../labs/03_real_rag/verification.md#minilm-local).
Они ещё не подключены к сквозному проекту. LLM evaluation — **NOT_RUN**:
generator согласуется отдельно. Teacher excerpt
callable не LLM. [Runtime recipe](../../../labs/03_real_rag/runtime.md) задаёт
следующую границу; [R08](../../../labs/05_model_serving/README.md) затем поставляет
выбранный serving runtime. Ученических отчётов/ответов здесь нет, статус освоения
не изменяется; самостоятельные материалы оцениваются вручную **REQUIRES_REVIEW**.
