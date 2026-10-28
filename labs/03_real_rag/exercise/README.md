# Самостоятельная вариация: инструкции мастерской

Задача отличается от teacher archive: выберите разрешённые инструкции о работе
небольшой мастерской, например бронирование инструмента, защитные очки и сдача
оборудования. Не используйте teacher corpus, готовые judgments или его ответы.
Укажите происхождение/разрешение, source IDs, revisions, роли и что считается
достаточным основанием ответа. Данные реальных людей/секреты не нужны.

Prerequisites: завершённые контракты
[rag-text-chunking](../../../modules/06_rag/exercises/text_chunking/README.md),
[rag-index-sync](../../../modules/06_rag/exercises/index_sync/README.md),
[rag-ranking-study](../../../modules/06_rag/exercises/ranking_study/README.md),
[rag-citation-validation](../../../modules/06_rag/05_grounded_answers/exercises/citation_validation/README.md)
и [rag-retrieval-regression](../../../modules/06_rag/exercises/retrieval_regression/README.md).
Они остаются самостоятельными TODO; готового решения под teacher alias здесь нет.

1. До выдачи напишите queries/judgments: буквальное совпадение, парафраз, вопрос без
   источника, противоречивые версии и вопрос о недоступном документе. Разделите
   группы на development/held-out до выбора chunking, k, pooling и no-answer policy.
2. Сравните lexical и реальный выбранный encoder на тех же доступных queries.
   Обоснуйте pooling по модели; после смены pooling создайте новый индекс. Random
   smoke не закрывает этот пункт. Покажите оба top-k списка, per-query ошибку и
   раздельный учёт вопросов без положительных judgments.
3. После отдельного выбора runtime создайте постоянный Qdrant index и проверьте
   restart, update, delete, доступ до top-k и повторную проверку context. Покажите
   отсутствие obsolete chunks, а не только новый point count.
4. Явно выберите generator. Зафиксируйте claim → quote → source/revision и no-answer
   при нехватке оснований. Измерьте provider outage/recovery; source injection
   не должен давать приложению право исполнять команды.
5. Независимо оцените retrieval и ответы. Ручная answer rubric: верность существенных
   утверждений, support каждого claim, актуальность, ACL, корректное воздержание,
   различение miss/absence/conflict/provider error. Проверка только ID/quote и
   LLM-as-judge недостаточны. Измерьте latency/cost в фактически выбранной среде.

Expected artifacts: exact corpus+provenance snapshot; queries/judgments и split;
model/tokenizer/preprocessing inventory; index identity; ingestion/restart evidence;
две выдачи и retrieval report; отдельные answers/citations/review; measurements;
краткое объяснение одной retrieval ошибки и одного неподдержанного claim.
Пишите под ignored `artifacts/` или `reports/`, не в source fixture.
[Пустой шаблон](report-template.md) не является выполненной работой.

Оценка вариации вручную: **REQUIRES_REVIEW**. Новый executable ID не добавлен;
teacher tests подтверждают авторскую механику, не присваивают освоение ученику.
Неподготовленные runtime/assets сохраняют NOT_RUN; они не заменяются fake-проходом.
