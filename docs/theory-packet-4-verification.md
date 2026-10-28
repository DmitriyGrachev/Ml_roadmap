# Теоретический пакет 4: материалы и проверка

Дата: 04.10.2026. Рабочая копия `C:\ProjectsDirectory\AIML\_road`, ветка
`codex/ai-ml-wave1`, HEAD `836028944eceaa260cb47d0056b593af4a4648d4`.
Это углубление шести существующих уроков, не новый курс. Понимание ученика
**НЕ ПРОВЕРЕНО**. Commit/push/merge не выполнялись.

## С чего начать и как проходить

Первым откройте [Module 04 README](../modules/04_machine_learning/README.md),
затем [Problem framing README](../modules/04_machine_learning/01_problem_framing/README.md)
и его theory.md. Порядок прежний: **01 постановка → 02 validation →
03 preprocessing → 04 модели → 05 оценка → 06 воспроизводимость**.

В каждом уроке: ответьте на прогноз до чтения результата → разберите пример
по шагам → запустите его → измените одну величину и объясните разницу →
переходите к указанному старому упражнению. Не нужно сначала разбирать весь
исходник сквозной демонстрации. Следуйте цепочке вопросов и таблицам уроков;
полный запуск уместен после evaluation, в reproducibility.

Из корня проекта, базовая среда:

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
uv sync --locked
uv run --offline --no-sync python -m modules.04_machine_learning.01_problem_framing.example
```

При переходе к уроку 06 — два **преподавательских** сценария, новая папка:

```powershell
uv run --offline --no-sync python -m modules.04_machine_learning.06_reproducibility.classical_demo --output reports/classical-demo-01
```

Необязательные графики, ещё одна новая папка:

```powershell
uv sync --locked --group visualization
uv run --offline --no-sync python -m modules.04_machine_learning.06_reproducibility.classical_demo --output reports/classical-demo-02 --plots
```

Установка может загружать пакеты при отсутствии кеша, но примеры не скачивают
модели/датасеты. Обычный числовой запуск не импортирует Matplotlib. Существующий
выходной каталог отвергается, даже пустой. Не открывается браузер, нет notebook
или скрытого состояния ячеек. После предыдущего запуска выбирайте новое имя
каталога, а не удаляйте старый результат.

Для самостоятельной работы используйте прежние задания и точные контракты,
например после своей реализации:

```powershell
uv run --offline --no-sync python scripts/learn.py test ml-model-comparison
uv run --offline --no-sync python scripts/learn.py check ml-model-comparison
```

`test` — разработческая проверка с допустимыми ожидаемыми xfail; `check ID`
требует завершения обязательных tests конкретного ID. Новая теория не расширяет
старый check. Далее — [tabular study](../modules/04_machine_learning/exercises/tabular_study/README.md)
и [evaluation case](../modules/04_machine_learning/exercises/evaluation_case/README.md)
по их prerequisites. Затем [математический мост](../modules/04_machine_learning/07_training_bridge/README.md)
→ [PyTorch](../labs/01_pytorch_foundations/README.md).
Prerequisite bridge у `ml-knn-mechanics` сохранён: объяснение геометрии в уроке
04 можно прочитать раньше, самостоятельную реализацию проходите по каталогу.

## Созданные и изменённые файлы

Новые файлы — 12:

- [01 framing/theory.md](../modules/04_machine_learning/01_problem_framing/theory.md).
- [02 validation/theory.md](../modules/04_machine_learning/02_validation/theory.md).
- [03 preprocessing/theory.md](../modules/04_machine_learning/03_preprocessing/theory.md).
- [04 models/theory.md](../modules/04_machine_learning/04_models/theory.md).
- [05 evaluation/theory.md](../modules/04_machine_learning/05_evaluation/theory.md).
- [06 reproducibility/theory.md](../modules/04_machine_learning/06_reproducibility/theory.md).
- [classical_demo.py](../modules/04_machine_learning/06_reproducibility/classical_demo.py).
- [complexity.png](../modules/04_machine_learning/06_reproducibility/assets/complexity.png) и
  [decisions.png](../modules/04_machine_learning/06_reproducibility/assets/decisions.png).
- [Lifecycle/экспорт/графики tests](../modules/04_machine_learning/tests/test_classical_demo.py).
- [Исполняемые фрагменты теории](../tests/integration/test_packet4_theory.py).
- Этот отчёт.

Изменены восемь существующих файлов: шесть README уроков 01–06 (входы в теорию),
[Module 04 README](../modules/04_machine_learning/README.md) (порядок и команды),
[wave2-coverage.md](wave2-coverage.md#theory-packet-4) (новый раздел с историей,
реальными файлами/ID и пятью свидетельствами покрытия).

Архитектура осталась прежней. Теория сопровождает уроки, а не создаёт параллельный
roadmap. Полностью разобраны преподавательские примеры; существующие examples,
сравнение ансамблей и статистические задания переиспользованы. Новый CLI
демонстрации — отдельный учебный запуск, основной `scripts/learn.py` не менялся.
Новых exercise ID и зависимостей нет. Авторские tests расположены вне старых
student targets и не являются автоматическим экзаменом текстовых ответов.

В demo только два небольших сценария: 96 независимых вымышленных поездок и
160 независимых машин. Это продолжение прежних нейтральных контекстов, **не**
данные support study и не его готовая реализация. Старые sensor examples с
40/80 строками — другие учебные выборки; они не выдаются за эту же когорту.

Схема датчиков явно делит train/selection/calibration/test (80/24/24/32).
FrozenEstimator не позволяет калибровке заново обучить базовый pipeline.
Гиперпараметры, вариант калибровки и threshold выбираются на development,
test не меняет конфигурацию. У поездок train/validation/test — 57/19/20.
Повторное использование selection делает development scores оптимистичными;
малый test не доказывает production-качество. Здесь holdout, а CV с новым fit
preprocessing на каждом fold разобрано отдельно в validation и старом задании.

Артефакт содержит pipeline вместе с preprocessing, raw schema/единицы/классы,
seed/версии/конфигурацию, кодовый hash, ID разбиения, dataset bytes, predictions
и метрики. Readable estimator parameters не заменяют learned coefficients:
обученное состояние находится в model.pkl. Представления объектов/`nan` в
конфигурации — строки для чтения, не инструкция для `eval` или загрузки.
Загрузка pickle допускается только для байтов своего объекта, только что
созданного этим вызовом. Checksum не устанавливает доверие. Нет arbitrary-load
CLI или tracking server.

## Техническая проверка

Среда: Windows, Python 3.12.14, NumPy 2.5.3, pandas 3.0.6, sklearn 1.9.1,
pytest 9.1.1, Matplotlib 3.11.2 в opt-in группе. До изменений полный набор
с visualization дал 963 passed, 39 skipped, 1160 xfailed, одно предупреждение.
Шесть исходных lesson examples также запускались с exit 0.

Все команды ниже выполнялись из корня. Непроведённые среды указаны отдельно.

| Проверка | Реальная команда/действие | Результат |
| --- | --- | --- |
| Базовая установка | `uv sync --offline --locked` | Успех из кеша; `find_spec('matplotlib')` и `find_spec('torch')` → None |
| Базовый полный regression | `uv run --offline --no-sync pytest -q` | 970 passed, 48 skipped, 1160 xfailed, 1 warning; 107.71 s |
| Связанный набор, база | `uv run --offline --no-sync pytest modules/04_machine_learning tests/integration/test_packet4_theory.py -q --tb=short` | 162 passed, 4 skipped, 138 xfailed |
| Новые author tests, база | `uv run --offline --no-sync pytest modules/04_machine_learning/tests/test_classical_demo.py tests/integration/test_packet4_theory.py -q --tb=short` | 14 passed, 2 skipped |
| Базовый mypy | `uv run --offline --no-sync mypy` | Success: 627 source files |
| Opt-in установка | `uv sync --offline --locked --group visualization` | Успех из кеша; восстановлен Matplotlib 3.11.2 |
| Opt-in полный regression | `uv run --offline --no-sync pytest -q` | 979 passed, 39 skipped, 1160 xfailed, 1 warning; 121.57 s |
| Новые author tests, visualization | Та же команда двух новых test-файлов | 16 passed |
| Mypy, visualization | `uv run --offline --no-sync mypy` | Success: 627 source files |
| Ruff | `uv run --offline --no-sync ruff check .` | All checks passed |
| Форматирование | `uv run --offline --no-sync ruff format --check .` | 818 files already formatted |
| Markdown и расчёты | `uv run --offline --no-sync python reports/packet4_verify.py` | 15 документов, 293 локальные ссылки/anchors, 21 таблица, 2 встроенных PNG; 11 независимых блоков, 48 примеров; ошибок нет |
| Внешние ссылки | `uv run --offline --no-sync python reports/packet4_links.py` | 22 URL официальной документации ответили HTTP 200 |
| Изображения | Просмотр двух сохранённых PNG; сравнение байтов со свежим экспортом | Читаемые оси/единицы/подписи; линия и матрица дополнительно проверены tests |
| Git whitespace | `git diff --check` | Успех |

QA-скрипты в `reports/` — локальные игнорируемые вспомогательные проверки,
не новая зависимость/часть CLI; после клонирования они не появятся. Постоянные
проверки расчётов, ссылок и поведения находятся в test-файлах репозитория.
HTTP 200 проверяет доступность страницы, не правильность всего её содержания.
Новые объяснения дополнительно сверены с первичной документацией sklearn:
validation/pipelines, linear models/neighbors/trees/ensembles, metrics/calibration
и model persistence. URL `stable` может измениться; версии локального запуска
указаны явно. Markdown проверен структурно, не во всех редакторах/браузерах.

### Что именно проверяют новые tests

- Непересекающиеся split ID покрывают все независимые наблюдения; test predictions
  следуют сохранённому порядку. Для этих demo единица — одна строка/одна машина,
  а повторные группы проверяет прежний `ml-group-safe-split`.
- Spy вокруг реального imputer.fit фиксирует только training ID; calibrator.fit
  видит только отдельные calibration ID. Это вызовы настоящего sklearn, не mock-модель.
- Подмена **только test targets при фиксированном split** меняет финальные
  метрики, но не выбор, development scores или predictions.
- Инференс отвергает переставленные/лишние feature columns; baseline и данные
  сохранены; SHA-256 совпадает с фактически записанными Windows CSV bytes.
- MAE, Brier и AP пересчитываются из saved predictions; decisions соответствуют
  frozen threshold. Support срезов покрывает test. Ручные confusion/MSE/RMSE/PR
  расчёты дополнительно выполняются как независимые transcripts.
- Два запуска с seed 31 воспроизводят predictions/выбор в этой среде;
  reload собственного pipeline даёт прежние predictions без расхождения.
- Геометрия линий depth/error и threshold/cost, значения confusion image берутся
  из сохранённых расчётов; test проверяет содержимое объектов Figure.
- Existing output не перезаписывается; отдельный subprocess числового CLI
  работает при принудительно недоступном импорте Matplotlib. PNG требуют opt-in.

Первые девять tests действительно падали до реализации нового файла, затем
прошли. Расширение конфигурации выявило `SimpleImputer.missing_values=NaN`:
строгий JSON отвергал число, исправлена только читаемая конфигурация, не запрет
NaN в метриках. Независимый review воспроизвёл этот сбой, затем подтвердил
10 passed для lifecycle tests после исправления. Review также выявил неверную
фразу о выборе метрики на validation: исправлена на выбор **порога**, основная
метрика/стоимости задаются до сравнения. Добавлен ручной reliability-bin разбор.

Первый полный базовый прогон был красным: `test_every_tracked_local_markdown_link_resolves`
обнаружил ссылку на ещё не созданный этот отчёт (1 failed, 969 passed, 48 skipped,
1160 xfailed). Файл создан; полный повтор дал результат в таблице. Проверки
не ослаблялись. В полных запусках сохраняется прежний DeprecationWarning
Starlette/AnyIO о `BlockingPortal`, присутствовавший до пакета.

Проверен старый смысл зачёта: `test ml-model-comparison` → 13 xfailed, exit 0;
`check ml-model-comparison` → `CHECK INCOMPLETE: xfails=13`, exit 1.
Это ожидаемые незавершённые ученические TODO, не ошибка пакета. Они не решены
ради зелёного check и не превращены в skipped tests.

### Измеренный преподавательский результат

Проверенные каталоги: числовой `reports/packet4-base-verified-01` (без
Matplotlib), визуальный `reports/packet4-demo-verified-02` (`--plots`).
Более ранний `reports/packet4-demo-01` — промежуточный запуск, не финальная
конфигурация экспорта. Папки сохранены, не перезаписаны.

CSV предсказаний базового и визуального запусков совпали побайтово для обоих
сценариев. Сохранённый code hash совпал с финальным `classical_demo.py`.
Разница между полными наборами — 9 plot-related skips: 7 прежних и 2 новых;
остальные skip/xfail не объявлены выполненными учеником.

- Поездки: выбран `ridge-0.1`; test `n=20`, MAE `2.368853` мин,
  RMSE `2.896028` мин, baseline MAE `13.900458` мин.
- Датчики: `C=1`, sigmoid, threshold `0.5`; test `n=32`, confusion
  `[[12,3],[3,14]]`, cost `3+4×3=15`, Brier `0.099188` против baseline `0.249375`.
- На тех же test строках ROC-AUC `0.941176`, **average precision** `0.949336`;
  это AP, не трапецеидальная PR-площадь. В отдельном ручном примере они различны:
  AP `5/6`, trapezoid `19/24`.

Метрики этих локальных синтетических данных не подтверждают пользу продукта.
Seed не подбирался ради победы сложной модели; tests не требуют определённого
победителя. Перенос между ОС/численными библиотеками с точностью до бита
не обещается.

## Что остаётся ученику и что не запускалось

Ученик самостоятельно защищает unit/as-of, split, выбор признаков и baseline,
цену ошибок, ограничения выводов, новый разумный эксперимент. Прогнозы до
запуска, вариации и объяснение ошибочного рассуждения проверяются вручную.
Зелёный pytest подтверждает технические свойства материалов, не освоение темы
и не качество вашей модели. Student implementations/reports не заполнены;
реальный learner ML evaluation — **NOT_RUN**, защита — **REQUIRES_REVIEW**.

Training/GPU/live, новые PyTorch/Hugging Face эксперименты, другие платформы,
browser rendering Markdown — **NOT_RUN**. Новых внешних моделей, датасетов,
frameworks или сервисов нет. Следующий редакционный пакет «обучение моделей
и Transformers» — **PLANNED**; предыдущий bridge используется ссылками.

Контроль SHA-256 всех 849 исходных неигнорируемых файлов: изменены только
восемь документов из списка; остальные **841 побайтово сохранены**. Добавлено
12 файлов. Сохранились предыдущие пакеты, все student TODO/реализации/отчёты,
`curriculum.toml`, CLI, `pyproject.toml`, `uv.lock`, progress. Hash progress:
`9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.
Игнорируемые runtime caches и `.venv` не входят в эту сверку; смена optional
окружения описана выше, итоговая среда оставлена с visualization.
