# Tracking, deployment и model lifecycle — спецификация

CORE на уровне одного сервиса · PLANNED. MLflow/drift tools не установлены этой волной.

Prerequisites: [две модельные labs](../../docs/roadmap.md),
[serving](../05_model_serving/README.md), модуль 08, SQL/CSV и versioned data protocol.

Expected artifacts: воспроизводимый data pipeline, annotation guide, snapshot и split
manifest, MLflow runs + локальное artifact storage/registry (tracking не заменяет
хранение), schema/preprocessing version, CI и deployment smoke, observability,
promotion policy, rollback script, runbook, короткий incident review.

Done: один и тот же preprocessing при train/inference; метрики связаны с реальными
файлами/версиями; повторная подготовка не дублирует данные. Canary/shadow promotion
контролируется человеком; rollback восстанавливает модель и нужный preprocessing/index.
Data drift отличается от concept drift; при отсутствии меток proxy signals
не доказывают потерю качества. Пример изменённого входа сопровождается планом
расследования, а не автоматическим retraining при каждом предупреждении.

Cloud essentials: одно облако, object storage, identities, minimal permissions,
secret handling, network boundary, контейнер, logs, budget и удаление ресурсов.
Платная установка необязательна. Kubernetes/Terraform/Spark/Airflow — OPTIONAL,
не prerequisites. Защита: что построено, как измерено, ограничения и trade-offs,
в том числе коротко на английском.
