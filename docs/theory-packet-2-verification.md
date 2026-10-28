# Теоретический пакет 2: материалы и журнал проверки

Дата: 04.10.2026. Репозиторий `C:\ProjectsDirectory\AIML\_road`, ветка
`codex/ai-ml-wave1`, исходный HEAD `836028944eceaa260cb47d0056b593af4a4648d4`.
Работа поверх незакоммиченного пилота и пакета 1, без замены на main.
Этот журнал описывает качество материалов, **не** прохождение учеником.

## Откуда начать

Откройте [README Pandas](../modules/03_data_foundations/02_pandas_core/README.md),
затем [теорию](../modules/03_data_foundations/02_pandas_core/theory.md).
Порядок: Pandas и старый пример → существующая практика группировок/соединений
→ [качество данных](../modules/03_data_foundations/03_data_quality/theory.md)
→ [EDA и четыре графика](../modules/03_data_foundations/03_data_quality/eda.md)
→ [самостоятельная погода](../modules/03_data_foundations/exercises/weather_quality/eda_practice.md).
После этого — практическая статистика и прежний маршрут.

Из корня репозитория:

```powershell
uv sync --locked
uv run --offline --no-sync python modules/03_data_foundations/02_pandas_core/example.py
uv run --offline --no-sync python modules/03_data_foundations/03_data_quality/example.py
uv sync --locked --group visualization
uv run --offline --no-sync python modules/03_data_foundations/03_data_quality/eda_demo.py --output reports/teacher-eda-01
```

Последний каталог должен быть новым. Демонстрация отказывается перезаписывать
существующий каталог; выберите другое имя при повторении. Свои скрипты,
картинки, реестр проблем и выводы размещайте в `reports/`, не в student starter.

## Что создано

Новые файлы относительно начала пакета 2:

- [Pandas theory](../modules/03_data_foundations/02_pandas_core/theory.md).
- [Quality theory](../modules/03_data_foundations/03_data_quality/theory.md).
- [EDA companion](../modules/03_data_foundations/03_data_quality/eda.md) и
  [исполняемая демонстрация](../modules/03_data_foundations/03_data_quality/eda_demo.py).
- Четыре генерируемых изображения в `modules/03_data_foundations/03_data_quality/assets/`:
  `distribution.png`, `relationship.png`, `groups.png`, `time.png`.
- [Погодный практикум](../modules/03_data_foundations/exercises/weather_quality/eda_practice.md),
  [описание источника](../modules/03_data_foundations/exercises/weather_quality/fixtures/README.md)
  и [исходный CSV](../modules/03_data_foundations/exercises/weather_quality/fixtures/eda_weather.csv).
- [Тесты EDA](../modules/03_data_foundations/tests/test_eda_demo.py) и
  [проверки примеров в текстах](../modules/03_data_foundations/tests/test_packet2_theory.py).
- Этот журнал.

Обновлены навигационные README модуля, Pandas, data quality; к weather README
добавлена только секция продолжения. Расширена [карта покрытия](wave2-coverage.md#theory-packet-2).
В `pyproject.toml` добавлена группа `visualization` с Matplotlib 3.11.2 и узкая
настройка mypy для отсутствующей opt-in библиотеки; обновлён `uv.lock`.
Старые версии зависимостей не менялись: добавлены Matplotlib и шесть его
зависимостей. Базовый набор зависимостей и группа `training` не расширены.

### Почему так

Теория сопровождает действующие `data-pandas` и `data-quality`, а не повторяет
уроки с новыми ID. Support tickets — полностью разобранный учительский пример;
weather — другой набор для самостоятельного переноса. Новое EDA-продолжение
оценивается вручную: существующий `check data-weather-quality` по-прежнему
проверяет только прежнюю функцию. Учительские tests находятся за пределами
student targets. Notebook не нужен: скрипт запускается с нуля и сохраняет
основания графиков вместе с результатом. Случайных данных и сетевой загрузки нет.

## Технические проверки

Среда: Windows, Python 3.12.14, uv 0.12.17, Pandas 3.0.6, NumPy 2.5.3,
Matplotlib 3.11.2 в opt-in окружении. Все команды — из корня репозитория.

Фактически выполненные проверки:

- `uv lock`, `uv sync --locked`, `uv sync --locked --group visualization` — exit 0.
  После базовой синхронизации `find_spec('matplotlib')` вернул `None`.
- `uv run --offline --no-sync pytest -q` с visualization —
  **946 passed, 39 skipped, 1160 xfailed**, итоговый полный прогон 101.88 s
  (предыдущий: 82.71 s). Предупреждение Starlette о deprecated AnyIO
  `BlockingPortal` существовало до пакета.
- После `uv sync --locked`, при подтверждённом отсутствии Matplotlib, тот же
  полный suite — **943 passed, 42 skipped, 1160 xfailed**, 86.99 s.
  Разница — ровно три новые opt-in проверки графиков. Непройденные student
  TODO не переименованы в успех. После проверки группа visualization установлена
  обратно; в оставленном окружении графики доступны.
- `uv run --offline --no-sync pytest modules/03_data_foundations/tests/test_eda_demo.py modules/03_data_foundations/tests/test_packet2_theory.py -q`
  — **10 passed**, последний прогон 4.04 s, в том числе после последнего
  пояснения CSV-чтения. Проверяются аудит/неизменность входа, разные выборки, конфликт
  ключа, non-finite/пустой вход, координаты/высоты, динамические n, реальные PNG,
  CSV/metadata и отказ от перезаписи; также все независимые pycon-сеансы.
- `uv run --offline --no-sync mypy` — **617 source files**, без ошибок,
  как с установленным Matplotlib, так и без него.
- `uv run --offline --no-sync ruff check .` — **All checks passed**;
  `uv run --offline --no-sync ruff format --check .` — **800 files already formatted**;
  `git diff --check` — exit 0.
- В редакционном QA выполнены **23 независимых pycon-блока / 135 проверяемых
  примеров**; CSV практикума механически проверен: 37 записей, 4 столбца.
- Учительская демонстрация реально запущена в новых каталогах
  `reports/packet2-teacher-20261004` и `reports/packet2-teacher-final-20261004`.
  Все четыре PNG просмотрены; подписи, единицы, легенды, n и отсутствие точки
  на дате с NA читаются. Табличные числа и графические отметки сверены тестами.
- Оба прежних `example.py` запущены: support-ticket summary имеет chat
  `(count=2, mean=11)` и email `(count=2, mean=35)`; quality example —
  `{'duplicate_document_ids': 1, 'missing_language': 1}`.
- `uv run --offline --no-sync python scripts/learn.py test data-weather-quality`
  — exit 0, **1 passed, 21 xfailed**.
  Та же команда с `check` вместо `test` — exit 1, **CHECK INCOMPLETE: xfails=21**.
  Это правильный отказ в зачёте незаполненной функции, а не неисправность пакета
  и не глобальная блокировка других заданий. EDA-продолжение в этот check не входит.

### Ссылки и отображение

Проверены **182 локальные ссылки/якоря в 11 документах**, включая карту и этот
журнал: цели существуют. **12 уникальных внешних URL** официальной документации
ответили HTTP 200 при `Invoke-WebRequest`; ссылки не требуют загрузки данных.
Проверка доступности не обещает, что будущая версия документации не изменится.

Markdown преобразован существующим Mistune с поддержкой таблиц, без установки
новой зависимости. В локальном браузерном предпросмотре просмотрены Pandas,
quality, EDA и погодный практикум; раскрытие ответов работает, переход
quality → EDA → practicum работает, все четыре изображения загружаются
как 1050 × 675. Таблица выравнивания и таблица частот рядом с графиком читаются.
Это проверка локального HTML-представления, **не** проверка отображения на
GitHub или во всех Markdown-редакторах/мобильных размерах. Вспомогательные
HTML и QA-скрипт лежат только в игнорируемом `reports/`; сервер предпросмотра
остановлен, отдельное приложение в программу не добавлено.

Локальная вспомогательная команда проверки ссылок/pycon/CSV и генерации
предпросмотра: `uv run --offline --no-sync python reports/packet2_verify.py`.
Это журнал авторской проверки в данной рабочей копии, не новый обязательный
инструмент курса; при клонировании игнорируемого скрипта не будет.
Постоянные воспроизводимые проверки примеров находятся в двух test-файлах выше.

В разработке сначала были зафиксированы падающие тесты отсутствующей
демонстрации, затем зелёные; отдельный тест обнаружил жёстко заданное n при
уменьшенном входе и прошёл после исправления. Первые lint/format проверки
нашли неоднозначное кириллическое слово в подписи, составной assert и длинные
pycon-строки — исправлено в новых файлах. Прямой запуск mypy на каталоге
с числовыми именами уроков дал duplicate-module; штатный package mode
`uv run --offline --no-sync mypy -p modules.03_data_foundations` прошёл (92 файла).

Независимый review текста исправил объяснение `kind` при сортировке по двум
столбцам и неоднозначную вариацию с удаляемым дубликатом; отдельный review
демонстрации сверил расчёты/PNG/экспорт/opt-in lock. Нерешённых замечаний в
проверенном объёме нет; это не аудит всей предыдущей рабочей ветки.

### Сохранность рабочей копии

Перед работой зафиксированы SHA-256 **824 существующих файлов**. Из них
изменились только семь перечисленных навигационных/config-файлов; остальные
**817 совпали побайтово**. Добавлено 14 файлов. Все прежние student реализации,
TODO, тесты контрактов, отчёты, Object Model и пакет 1 сохранены. `curriculum.toml`
и код CLI не изменены, реестр содержит те же **162 ID**. В weather README
добавлена секция, прежнее условие задачи не переписано.

SHA-256 `progress.md` до и после:
`9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.
Commit/push/merge не выполнялись. Никаких моделей и сетевых датасетов не скачано.

## Что остаётся проверить ученику

Технически исправный пример не доказывает ваше понимание. Прогнозы по
alignment, cardinality, группам и пропускам, самостоятельные вариации и
объяснения — **REQUIRES_REVIEW**. Погодный анализ, его решения и графики —
**NOT_RUN учеником / не оценены**. Ваши итоговые наблюдения и отчёты не заполнены.

Для каждого своего графика нужны вопрос, конкретное наблюдение и граница
вывода. Код должен воспроизводить выборку и сохранять исходник. Маленькие
вымышленные данные не доказывают свойства реальной погоды или службы поддержки.
Новый графический интерфейс, виджеты и дополнительные plotting-библиотеки
не создавались. Остальные редакционные пакеты остаются **PLANNED**.
