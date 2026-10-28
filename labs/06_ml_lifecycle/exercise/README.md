# Независимая ручная вариация: исчезнувшие bytes и поздняя разметка

Самостоятельная граница **REQUIRES_REVIEW**, runtime evidence пока NOT_RUN.
Это не новый автоматический exercise ID и не решение старых release-gate/
artifact-manifest/data-release TODO. Их prerequisite реализации выполняются отдельно.

Возьмите свой завершённый Document Intelligence classifier bundle, а не teacher
shapes. В новом экспериментальном каталоге сохраните original и candidate release
с независимым внешним decision record. Выберите **два разных случая**:

- Metadata доступны, а одна copy model bytes потеряна. Покажите fail-closed
  restore и recovery из заранее сохранённой совместимой копии в новом destination.
  Не удаляйте originals, реальные datasets или пользовательские artifacts.
- Увеличилась доля коротких входов; labels приходят позже и только для части window.
  Выберите собственные маленькие finite windows, сохраните actual predictions/time
  и раздельные count/labeled_count. Не выдавайте constructed labels за live feedback.

До запуска предскажите, какие assertions и выводы изменятся. Не меняйте порог
после просмотра результатов. Назовите human hold/promotion/rollback решение,
реальную readiness/parity проверку и границу model/preprocessing/index.
Проанализируйте, что нельзя заключить о качестве до labels и при biased label sample.
Если memory-aware data prerequisite ещё не закончен, отметьте этот gate открытым;
tiny teacher demo его не заменяет. Не устанавливайте MLflow/Qdrant/сервисы ради отчёта
без отдельной подготовки runtime. Для registry сохраните честный NOT_RUN.

Заполните [пустой report](report-template.md) своими командами и actual evidence.
Человек проверяет provenance/rubric/split, повторяемость, denominators, failure,
actual restarted prediction, причины действий и ограничения. Teacher unit tests,
хеш собственного отчёта и красивый график не подтверждают освоение.
