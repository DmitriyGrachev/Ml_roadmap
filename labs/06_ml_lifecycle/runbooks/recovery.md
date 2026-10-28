# Локальное восстановление и incident record

Рабочая инструкция для teacher classification bundle. Время ответа не выбирает
версию автоматически. Решение человека и expected digest записываются **до**
проверки инцидентного пакета. Live deployment и index compatibility — NOT_RUN.

1. Ограничьте влияние по заранее принятой политике, сохраните incident ID, window,
   release/model/preprocessing identity, ошибки и состояние labels. Не пишите
   чувствительный raw text в журнал без причины и политики хранения.
2. Проверьте artifact availability, schema/config, actual bytes, runtime versions.
   Недоступные bytes при здоровом registry — отдельная failure storage.
3. Получите прежний release digest из независимого operator record. Выберите
   classification-only A целиком; не смешивайте model B и preprocessing A.
4. `restore_release_new` с **новым** destination проверяет release/bundle, копирует
   inventory, запускает shared service lifespan, replay/readiness и реальный probe.
   Для sklearn pickle отдельно требуется доверие к локальному издателю; hash не
   разрешает executable deserialization. Ошибка startup не создаёт success report;
   partial output не переиспользуется, для retry выбирается новый destination.
5. Убедитесь, что `restart.json` относится к ожидаемому digest и что actual response
   `triangle → circle` для teacher A. Ответ — проверка выбранного поведения, а не
   ground truth quality gate. Повторите startup из сохранённого operator config
   в новом процессе через [существующий service](../../../projects/document_intelligence_lab/service/README.md).
6. Для production release отдельно подтвердите representative quality/slices,
   rollout/traffic policy, privacy, budget, index compatibility и actual deployment
   smoke. Человек решает переключение. Local TestClient этих фактов не доказывает.
7. Разберите временную шкалу, причину, почему gate пропустил проблему, минимальное
   предотвращение и проверку восстановления. Не приравнивайте alert к retrain.

Вызов narrow author API из уже доверенного локального Python окружения:

```python
from importlib import import_module
from pathlib import Path

releases = import_module("labs.06_ml_lifecycle.releases")
releases.restore_release_new(
    Path("artifacts/MY_RUN/release-A"),
    Path("artifacts/MY_NEW_RECOVERY"),
    expected_release_sha256=operator_recorded_digest,
)
```

`operator_recorded_digest` — ранее сохранённый lowercase SHA-256, не значение,
самостоятельно заявленное непроверенным bundle. Existing destination вызывает
FileExistsError; исходные bytes сохраняются. `verify_release` не требует
исходного absolute path: release переносится как единый каталог.

Пустые поля для самостоятельного incident record находятся в
[report-template](../exercise/report-template.md). Его содержание проверяет человек.
