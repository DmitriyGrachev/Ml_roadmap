# Самостоятельно: воспроизведите эксперимент с объявлениями

ID: `document-a1-reproduction`, kind: `exercise`. Новое умение — связать и
воспроизвести собственный document experiment, включая перенос bytes в новый процесс.
Split/метрики/preprocessing уже изучены в [пререквизитах A1](../README.md).
Teacher `demo.run_demo` нельзя вызывать как решение: у вас другие texts/labels/study.

В [fixtures/data.json](fixtures/data.json) — 18 авторских библиотечных объявлений.
Ordered labels: borrowing/access/event. [Правила аннотации](fixtures/annotation-guide.md),
[sources/permission](fixtures/sources.json), [fixed splits](fixtures/splits.json).
Данные нельзя менять ради лучшего score. Train = 9, validation = 3, test = 6.
Новая вариация требования: цена ошибки access → event выше остальных; объясните,
достаточно ли текущей выборки для нового выбора и какой следующий study нужен.

Реализуйте только [starter.py](starter.py)::`run_reproduction(fixtures, output, seed=23)`.
При новом output создайте свои rules и train-only sklearn Pipeline, сравните на
validation и зафиксируйте выбор до test. Используйте общие [helpers](../../artifacts.py)
для целостности/метрик, не переписывайте их. Не копируйте готовые teacher decisions.
Улучшение baseline не обязательно. Не импортируйте `test_evidence.py` как решение:
его слабые модели служат тестовыми данными валидатора, не заданным learner pipeline.

Контракт результата — новый output с `rules/`, `tfidf-linear/`, `report.json`.
Два bundles соответствуют [schema 1](../schema.md), одному data/split/source identity
и seed. `exercise_id='document-a1-reproduction'`,
`evidence_kind='STUDENT_OFFLINE_REPRODUCTION'`. Record code revision/dirty/source hash,
versions/config/preprocessing/model identity; реальные fit/inference seconds;
если память не измерялась, `null` и причина. Повтор output должен вызвать
`FileExistsError`; новый run с тем же seed сохраняет test predictions.

Report (создаётся вами, здесь не заполнен): `schema_version=1`, тот же exercise_id,
`bundles={rules:{path,manifest_sha256},tfidf-linear:{path,manifest_sha256}}`,
`analysis` с непустыми полями `source_permission`, `annotation_ambiguity`,
`selection_reason`, `error_analysis`, `changed_requirement`.
Пути bundle — relative portable directories внутри output, digest относится к
завершённому manifest. Выберите rules, подходящие вашему объяснению; fixture test
не требует заранее известного score и не награждает высокую accuracy.

Вызовите `validate_reproduction(output, trusted_local_artifact=True)` только после
осознанного доверия собственному локальному producer. Такой flag не предназначен
для загруженного чужого report/pickle. Скопируйте bundle в новый каталог и проверьте
reload в новом процессе. Expected digest берите из заранее выбранной локальной
конфигурации/сохранённого reference, а не из inference request.

Проверки из корня, после регистрации ID контроллером:

```powershell
.venv/Scripts/python.exe -m roadmap_tools test document-a1-reproduction
.venv/Scripts/python.exe -m roadmap_tools check document-a1-reproduction
```

Точные required targets: `part_a1/exercise/test_starter.py` и
`part_a1/exercise/test_evidence.py` внутри `projects/document_intelligence_lab/`.
Normal test допускает xfail только от `NotImplementedError` starter.
Strict check должен отклонить незавершённую работу. Validation готового malformed
artifact вызывает обычный fail, а не xfail. Teacher tests не являются зачётом ученика.

Для защиты используйте [пустые вопросы](report-template.md). Объясните фактические
ошибки с row IDs, почему validation не равен test, и что изменит новое требование.
Валидатор проверяет bytes/schema/метрики/replay; независимость выбора, качество
объяснений и перенос на новую задачу остаются `REQUIRES_REVIEW`.
[CI](../../../../docs/continuous-integration.md) не меняет progress за вас.
