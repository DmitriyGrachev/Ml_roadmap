# 05. LangGraph управляет шагами, MCP переносит вызов

Практическая проблема: наш локальный процесс уже имеет state, переходы, проверку права и имитацию инструмента. Что изменит framework для графа и зачем отдельный протокол вызова инструмента? До примера предскажите: станет ли найденный MCP tool автоматически разрешённым для посетителя?

Интуиция: LangGraph помогает организовать **state → nodes → edges → finish**. MCP описывает границу между host/client и server: какие tools сервер объявляет, каков input schema и как возвращается результат. Это разные ответственности. MCP не является агентом, discovery не выдаёт permission, описание инструмента не становится доверенной инструкцией. В Java/Spring аналогия — workflow/service orchestration против протокола удалённого service call; и там, и здесь policy остаётся у приложения. Модель, если она есть, лишь предлагает выбор и может ошибиться.

В уже существующем [`example.py`](example.py) — **реальный локальный framework example**, не симуляция MCP. `GraphState` (`TypedDict`) имеет `topic` и `label`; узел `normalize_topic` возвращает обновление `topic`; узел `prepare_label` возвращает `label`. `StateGraph(GraphState)` добавляет узлы и рёбра `START → normalize → label → END`, `compile().invoke(...)` запускает фиксированный порядок. На `topic="  Astronomy  "` результат `Catalog request: astronomy`. Здесь нет модельного выбора, ветвления, checkpointer и внешнего эффекта. `tracing_context(enabled=False)` удерживает LangSmith tracing выключенным внутри примера.

Отдельно `MCPServer("Local Museum")` регистрирует `lookup_exhibit(exhibit_id)`. `Client(server)` в async context использует **in-process transport SDK**, без порта, процесса и сети. Клиент после входа видит capabilities, `list_tools()` выдаёт имя и требуемый `exhibit_id`, `call_tool("lookup_exhibit", {"exhibit_id":"E-001"})` возвращает `Brass telescope`, затем контекст закрывает соединение. Это проверяет локальный lifecycle SDK и boundary инструмента; не доказывает работу с внешним сервером, аутентификацию или production transport. Закреплённые пакеты проекта: LangGraph 1.2.12, MCP Python SDK 2.2.0, LangSmith 0.14.0.

| Вопрос | LangGraph в примере | MCP в примере | Решение приложения |
| --- | --- | --- | --- |
| Порядок | рёбра фиксируют два узла | не задаёт workflow | может задавать ветвление/лимиты |
| Данные | state updates | tool request/result | проверяет schema, права и provenance |
| Конец | `END` | результат одного вызова | оценивает цель и остановку |

Соотнесите с G-01: proposal напоминания могла бы быть результатом узла или модели внутри узла, а вызов разрешённого tool мог бы пройти через MCP. Ни граф, ни protocol не освобождают от exact approval, recheck прав, operation limits, budget и проверки результата. Наш [`walkthrough.py`](../walkthrough.py) остаётся маленьким явным процессом без нового графа или MCP сервера. Это предохраняет сравнительный сценарий от превращения в новый SDK курс.

Типичная ошибка — увидев input schema при `list_tools()`, считать её проверкой полномочий. Server описал формат, host и приложение ещё должны решить, может ли данный user сделать данный вызов. Возвращённый текст инструмента тоже данные, потенциально с инструкционно выглядящим содержимым. Не выполняйте его как код или политику.

Практика: [tool dispatch](../02_tools_permissions/exercises/tool_dispatch/README.md), ID `agents-tool-dispatch`, и [bounded loop](../03_bounded_agents/exercises/bounded_loop/README.md), ID `agents-bounded-loop`, оставляют границы проверки ученику. Вариация: в локальном примере поменять `topic` на строку с пробелами и предсказать label; затем указать, где вокруг MCP-вызова пришлось бы поставить проверку права, если tool стал бы consequential.

Самопроверка: что такое node update? Что делает edge? Какую роль играет `END`? Что именно сообщил MCP schema? Почему in-process проверка не подтверждает сетевой deployment? Кто решает, допустим ли `call_tool` для пользователя?

Источники: LangChain, [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), англ., state/nodes/edges/compile; MCP Python SDK, [Client lifecycle](https://py.sdk.modelcontextprotocol.io/client/), англ., context/list/call. Источники относятся к закреплённым API примера, а не к будущей инфраструктуре.
