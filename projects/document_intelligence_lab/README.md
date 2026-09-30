# Document Intelligence Lab — проектная спецификация

CORE capstone · PLANNED. Это будущая самостоятельная работа, не готовое портфолио.
[Banking AI Lab](../banking_ai_lab/README.md) сохраняется без изменений.

Часть A: классификация публичных/синтетических документов или обращений — правила,
classical ML, pretrained encoder; prerequisites: [ML](../../modules/04_machine_learning/README.md),
[PyTorch](../../labs/01_pytorch_foundations/README.md),
[Hugging Face](../../labs/02_huggingface_models/README.md).
Часть B: RAG по разрешённой документации — prerequisites: модуль 06 и
[Real RAG](../../labs/03_real_rag/README.md). Позже bounded workflow (модуль 07)
и [serving](../../labs/05_model_serving/README.md), не произвольный автономный агент.

Expected artifacts: problem brief, data/model manifests, два evaluation протокола,
сравнение baseline, классификатор с reload, corpus/index и citations, architecture
note, error analysis, resource/cost report, ограничения, learner presentation.

Done: все решения объяснены автором, quality измерено на независимых данных;
классификация не оценивается только retrieval metric и наоборот. Проверены
no-answer, permissions, отказ внешней модели и восстановление. Выбор online/batch,
API/self-hosting, training/retrieval обоснован quality/latency/cost.
Нет реальных персональных данных, секретов в логах, исполнения модельного кода
или доверия prompt/regex как гарантии безопасности. Опасные действия требуют
подтверждения; инструменты allowlisted и выполнение ограничено.
