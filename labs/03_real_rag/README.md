# Real RAG — спецификация

CORE Applied AI · PLANNED. Здесь нет реализованной лабораторной или зачёта.

Prerequisites: [Hugging Face](../02_huggingface_models/README.md),
[модуль 06](../../modules/06_rag/README.md), ACL/citations и [протокол данных](../../docs/experiment-protocol.md).

Построить разрешённый corpus технической документации, настоящие embeddings,
постоянный Qdrant index и один явно выбранный local/external LLM provider.
Использовать существующие chunking/ranking/permissions/citations как контракты.
Не считать инструкции внутри документов или tool output доверенными командами.

Expected artifacts: snapshot+manifest, annotation queries/relevance labels,
ingestion/update/delete pipeline, lexical baseline, retrieval report и отдельный
answer report с citations/no-answer, latency/cost и ручной проверкой части ответов.

Done: зафиксированы Recall@k/MRR или nDCG по смыслу задачи; сравниваются lexical,
embeddings, chunking и metadata/ACL filtering; hybrid/reranking вводятся только
при измеренной пользе. Проверены удаление, обновление, отсутствие источника,
невозможность выдачи чужого документа. LLM-as-judge не единственная истина.
Любые внешние расходы требуют отдельного выбора пользователя.
