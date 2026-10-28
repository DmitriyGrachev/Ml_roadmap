# MLflow registry: локальный учебный запуск и release recipe

Для локального учебного lifecycle подготовлено отдельное окружение
`.venv-tracking` с MLflow 3.17.0: [реальная регистрация, pins и rollback](../../../projects/document_intelligence_lab/tracking_intro/registry-lifecycle.md).
Ниже — **recipe полного release promotion**; он не выполнялся на production
service или RAG index. Сначала выполните существующий
[R04 actual runs/flavor/restore](../../../projects/document_intelligence_lab/tracking_intro/README.md).
Его `track_bundle` возвращает `run_id`, `model_uri`, `bundle_sha256`; reused flavor
принимает **normalized strings**, полный raw-text preprocessing остаётся в bundle.

Следующий фрагмент исполняется только после успешного R04 actual roundtrip.
Все переменные берутся из operator record и результата `track_bundle`:

```python
import mlflow
from mlflow import MlflowClient
from projects.document_intelligence_lab.tracking_intro.demo import local_store

uri, _ = local_store(database, artifact_root)  # absolute local SQLite + files
mlflow.set_tracking_uri(uri)
mlflow.set_registry_uri(uri)
client = MlflowClient(tracking_uri=uri, registry_uri=uri)
version = mlflow.register_model(tracked["model_uri"], registered_name)
client.set_model_version_tag(
    registered_name, version.version, "bundle_sha256", tracked["bundle_sha256"]
)
client.set_model_version_tag(
    registered_name, version.version, "release_sha256", verified_release_digest
)
```

Здесь остановитесь: человек проверяет quality, compatibility, actual restore и
readiness, сохраняет previous version/digest и решение. Только отдельное явное
действие оператора после этих проверок выполняет promotion:

```python
client.set_registered_model_alias(registered_name, "champion", version.version)
```

Сохраните прежний numeric version и **внешний release digest** до изменения alias.
Для rollback сначала восстановите full prior bundle через R04 `restore_run_new`
в NEW storage, проверьте release identity и фактический service restart по runbook,
затем отдельным human action верните alias на прежний version. Отмена alias без
проверенного deployment не доказывает откат. Для RAG нужен index bundle; `null`
у teacher означает отсутствие проверки. Не вычисляйте release digest из registry
tag как единственный источник доверия; tag — mutable metadata.

Будущая actual проверка: две real runs и доступные artifacts, real sklearn flavor
reload, registration, prior version record, восстановление bytes в новом каталоге,
human-gated alias change/rollback и реальный restart с прежним ответом. Missing
artifact и несовместимый preprocessing обязаны блокировать promotion. Никакой
mocked tracker или JSON imitation не закрывает этот gate. Перед исполнением
сверьте APIs с выбранной установленной версией MLflow.

Источники: MLflow [registry workflow](https://mlflow.org/docs/latest/ml/model-registry/workflow/)
(registration/version/aliases) и [client API](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.client.html)
(`set_model_version_tag`, `set_registered_model_alias`), англ.; просмотрены
2026-10-11. Registry требует database backend; bytes отдельно от metadata.
Читать до локальных registration/alias операций, без remote cloud/server setup.
