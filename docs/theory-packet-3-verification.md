# Теоретический пакет 3: материалы и проверка

Дата: 04.10.2026. Рабочая копия `C:\ProjectsDirectory\AIML\_road`, ветка
`codex/ai-ml-wave1`, HEAD `836028944eceaa260cb47d0056b593af4a4648d4`.
Это углубление двух существующих уроков; не новая волна специализаций.
Commit/push/merge не выполнялись. Состояние ученика не засчитывается авторскими tests.

## Что открыть и в каком порядке

Часть A: [Practical statistics — README](../modules/03_data_foundations/04_practical_statistics/README.md),
затем [теория](../modules/03_data_foundations/04_practical_statistics/theory.md) §1–8.
Нужны предыдущие NumPy, Pandas, качество данных и опыт EDA, но не ML/bridge.
Сначала прогноз/ручной расчёт, затем разобранный код, затем собственная вариация
и прежние `data-statistical-profile`, `data-bayes-alert`, `data-paired-observations`.

Часть B: [Training bridge — README](../modules/04_machine_learning/07_training_bridge/README.md),
затем [теория](../modules/04_machine_learning/07_training_bridge/theory.md).
Prerequisites: NumPy, ML problem framing, validation/split/leakage,
models/regression/baseline, evaluation. Мост остаётся после этих тем, перед
PyTorch. Сначала скалярный ручной проход, затем старый `example.py`, новая трасса,
самостоятельные вариации и свой векторный TODO `ml-training-bridge`.

Все команды ниже — из корня проекта. В существующем базовом окружении:

```powershell
Set-Location C:\ProjectsDirectory\AIML\_road
uv sync --locked
uv run --offline --no-sync python -m modules.03_data_foundations.04_practical_statistics.stats_demo
uv run --offline --no-sync python -m modules.04_machine_learning.07_training_bridge.descent_demo
```

Последнюю команду запускайте только при переходе к части B, не как prerequisite
статистики. Для PNG используйте имеющуюся opt-in группу и **новые** каталоги:

```powershell
uv sync --locked --group visualization
uv run --offline --no-sync python -m modules.03_data_foundations.04_practical_statistics.stats_demo --output reports/stats-demo-01
uv run --offline --no-sync python -m modules.04_machine_learning.07_training_bridge.descent_demo --output reports/descent-demo-01
```

Без `--output` нет записи файлов и импорта Matplotlib. С ним сохраняются PNG,
CSV, параметры и версии; статистика также сохраняет все случайные выборы и
SHA-256 **байтов** `latencies.csv`. Имеющийся каталог отклоняется, даже если пуст.
`uv sync` может скачивать пакеты при отсутствии кеша, но не модели/датасеты.
Браузер не открывается. Notebook, виджетов и новых зависимостей нет.

Для своих реализаций выбирайте только нужный существующий ID, например:

```powershell
uv run --offline --no-sync python scripts/learn.py test data-statistical-profile
uv run --offline --no-sync python scripts/learn.py check data-statistical-profile
uv run --offline --no-sync python scripts/learn.py test ml-training-bridge
uv run --offline --no-sync python scripts/learn.py check ml-training-bridge
```

`test` допускает существующие xfail; `check` требует выполненный student contract.
Ни один из этих старых check не засчитывает новые текстовые ответы.

## Создано и изменено

Изменены только существующие точки входа двух уроков и текущая карта покрытия:

- [Statistics README](../modules/03_data_foundations/04_practical_statistics/README.md).
- [Bridge README](../modules/04_machine_learning/07_training_bridge/README.md).
- [Карта покрытия: отдельный актуальный раздел](wave2-coverage.md#theory-packet-3).

Новые файлы:

- [Статистика: theory.md](../modules/03_data_foundations/04_practical_statistics/theory.md),
  [stats_demo.py](../modules/03_data_foundations/04_practical_statistics/stats_demo.py),
  [outlier.png](../modules/03_data_foundations/04_practical_statistics/assets/outlier.png),
  [sampling.png](../modules/03_data_foundations/04_practical_statistics/assets/sampling.png).
- [Мост: theory.md](../modules/04_machine_learning/07_training_bridge/theory.md),
  [descent_demo.py](../modules/04_machine_learning/07_training_bridge/descent_demo.py),
  [descent.png](../modules/04_machine_learning/07_training_bridge/assets/descent.png).
- [Числа/экспорт/графики статистики](../modules/03_data_foundations/tests/test_statistics_demo.py),
  [Скалярная трасса/экспорт/график](../modules/04_machine_learning/tests/test_descent_demo.py),
  [Независимые кодовые фрагменты теории](../tests/integration/test_packet3_theory.py).
- Этот журнал.

Архитектура: дополнительные `theory.md` рядом с прежними README и фиксированные
teacher demos. Скалярный мост **импортирует** прежние `loss`, `gradient`, `step`.
Нет общей реализации профиля, Bayes-alert или векторного `gradient_step` за ученика.
Новые author tests находятся вне старых student test targets; ID и объём check
не расширены. Исторические записи карты сохранены; следующий пакет
«классическое ML и оценка» остаётся **PLANNED**.

## Техническая проверка

Версии: Python 3.12.14, NumPy 2.5.3, Pandas 3.0.6, Matplotlib 3.11.2 (opt-in),
uv 0.12.17. Базовый regression до изменений: 946 passed, 39 skipped,
1160 xfailed. Далее — только фактически выполненные проверки.

| Проверка | Команда/действие | Результат |
| --- | --- | --- |
| Новые author tests | `uv run --offline --no-sync pytest modules/03_data_foundations/tests/test_statistics_demo.py modules/04_machine_learning/tests/test_descent_demo.py tests/integration/test_packet3_theory.py -q --tb=short` | 17 passed с visualization |
| Базовый install | `uv sync --offline --locked` | Успех; Matplotlib отсутствует, проверено через `find_spec` |
| Базовый regression | `uv run --offline --no-sync pytest -q` | 956 passed, 46 skipped, 1160 xfailed; финальный повтор 97.21 s |
| Базовый mypy | `uv run --offline --no-sync mypy` | Success: 624 source files |
| Opt-in install | `uv sync --offline --locked --group visualization` | Успех из локального кеша, Matplotlib 3.11.2 |
| Opt-in regression | `uv run --offline --no-sync pytest -q` | 963 passed, 39 skipped, 1160 xfailed; финальный повтор 106.24 s |
| Ruff | `uv run --offline --no-sync ruff check .` | All checks passed |
| Форматирование | `uv run --offline --no-sync ruff format --check .` | 808 files already formatted |
| Mypy с visualization | `uv run --offline --no-sync mypy` | Success: 624 source files |
| Ссылки/Markdown | `uv run --offline --no-sync python reports/packet3_verify.py` (локальный авторский QA, игнорируется Git) | 6 документов, 203 локальные ссылки/anchors, 9 таблиц, 3 встроенных PNG; 7 независимых блоков, 31 doctest-пример |
| Изображения | Три PNG просмотрены; подписи, легенды, единицы, отсутствие перекрытия данных | Выполнено; координаты и высоты отдельно проверены tests |

В обоих полных прогонах одно прежнее предупреждение Starlette/AnyIO о
`BlockingPortal`, присутствовавшее до пакета. Разница 7 skipped между окружениями —
три прежних EDA plot tests и четыре новых plot/export tests. Остальные прежние
skip/xfail не скрыты и не объявлены выполненными учеником. `git diff --check`
также пройден. Итоговое окружение оставлено с opt-in visualization.

Независимый review проверил математику/педагогику и код/экспорт. Найденные
замечания исправлены: ручной пример повторных выборок, отсутствие готовых
ответов к самопроверке, путь PNG, стиль и точный Windows CSV hash. Для последнего
новая проверка сначала реально упала, затем прошла после исправления записи
байтов. Проверки не ослаблялись.

Отдельный запуск `uv run --offline --no-sync pytest tests/integration/test_packet3_theory.py -q --tb=short`
выявил зависимость нового теста от порядка сбора модулей в pytest importlib mode.
Исправлена только подготовка пути импорта в author test через `monkeypatch`;
изолированный повтор дал 2 passed, базовый новый набор — 13 passed/4 skipped.
Оба полных regression затем повторены. Учебный пример и правила pytest не менялись.

Смысл прежнего зачёта проверен отдельно реальными командами:
`uv run --offline --no-sync python scripts/learn.py test ml-training-bridge`
дал 1 passed/14 xfailed, exit 0; та же команда с `check` —
`CHECK INCOMPLETE: xfails=14`, exit 1. Это ожидаемый незавершённый student TODO,
не ошибка созданного пакета и не повод решать за ученика. Progress не меняется.

Реальные числовые запуски: `stats_demo` без экспорта и с
`--output reports/packet3-stats-verified-02`; `descent_demo` без экспорта и с
`--output reports/packet3-descent-verified-01`. Финальные PNG в уроках скопированы
из этих результатов. Повторный вывод в тот же каталог проверен тестом: отказ,
сохранённые байты не меняются. Первый статистический QA-каталог `...-01` был
промежуточным до исправления Windows newline/hash, не считается финальным.

Контрольные числа:

- Статистика: среднее `12→68.6`, медиана `11→11`, дисперсия `10→13390.24`
  (`ddof=0`), стандартное отклонение `3.162278→115.716205` минуты.
- Байес: `P(B|M)=30/40=0.75`, обратная доля `30/42≈0.714286`.
- Seed 2026: средние 500 оценок при n=5/50 — `12.07000`/`12.00784`;
  их эмпирические стандартные отклонения `1.352375`/`0.452957` (`ddof=1`).
  Tests не требуют победителя или «идеальной» случайной метрики.
- Мост: `a=0.7`, `p=1.4`, `e=-1.6`, `L=2.56`, `g=-6.4`;
  rate 0.05 даёт `a=1.02`, `L=0.9216`; 0.25 — цикл; 0.3 — рост loss.
- Центральная разность при ε=1e−6 дала ошибку около `1.84e−10`, при
  ε=1e−16 — около `0.2613`. Это диагностика float на этой платформе, не гарантия
  для любого ε или любой функции.

Первичные источники: официальные NumPy Statistics API/var/quantile/choice/cov,
OpenIntro Statistics (страница книги и указатель разделов), D2L §2.4 Calculus.
Условие, независимость и Байес дополнительно сверены с открытым исходником
официальных слайдов OpenIntro §3.2; старое предупреждение про logits — с PyTorch
2.14 `CrossEntropyLoss`. Источники проверены как текст, не через браузерный интерфейс.
Официальные HTML-страницы доступны; прямой PDF OpenIntro через redirect не удалось
получить (timeout), поэтому он не объявлен прочитанным. В статистике оставлены
две внешние ссылки, в мосте одна, с целью и границей чтения.

## Что не является результатом ученика

Расчёт другой выборки, прогноз перед запуском, разбор неверного объяснения,
обоснование единицы/отбора/IID, ограничения корреляции и ответ про validation
проверяются **вручную**. Никакого автоматического экзаменатора текста нет.
TODO, student implementations и итоговые отчёты не заполнялись.

Не проведены: проверка понимания учеником, реальное ML evaluation, обучение
моделей, новые PyTorch/Hugging Face эксперименты, браузерный просмотр Markdown.
PNG проверены визуально, а Markdown — структурно; это не проверка отображения
во всех редакторах. Новые функции не оценивались на чужих реальных данных.

Сверка SHA-256 838 исходных неигнорируемых файлов: изменены только два README
из перечня выше и `docs/wave2-coverage.md`; остальные 835 сохранились побайтово.
Добавлено 11 файлов, перечисленных выше. Сохранились все исходные TODO/реализации,
пакеты 1–2 и Object Model, `curriculum.toml` (162 ID), CLI, `pyproject.toml`,
`uv.lock` и `progress.md`. SHA-256 progress:
`9C78D95D05EFB7234C8B3412D072577916A11192531AEE1B27A0DF60CE647DC0`.
Проверка хешей не охватывает содержимое игнорируемой `.venv` и runtime-кешей;
изменение набора установленных optional пакетов описано выше.
