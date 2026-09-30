# Введение в прогноз на один день

Prerequisites: `data-time-split`, `ml-time-series-split`, `ml-models`, `ml-evaluation`.
См. [data foundations](../../../03_data_foundations/README.md),
[time-series split](../../exercises/time_series_split/README.md),
[модели](../../04_models/README.md), [оценка](../../05_evaluation/README.md).

Прогнозируем дневное число обращений. В origin t известно только прошлое до t−1
включительно и календарь t. Horizon строго **один день**: предсказывается count[t].
После наступления следующего дня фактическое наблюдение можно использовать для
нового origin. Это rolling one-step evaluation, не прогноз сразу на две недели.
Multi-step с actual-future lag здесь вне scope, не добавляйте его молча.

## Editable files и контракт

Реализуйте две функции в `starter.py`, собственные вспомогательные модули допустимы.
Fixture, example, tests и evidence validator не меняйте. Данные локальные,
маленькие и детерминированные: `fixture.daily_counts()`, ровно 84 дня с 2024-01-01;
`dataset_bytes()` задаёт точные bytes исходного `data.json`.

`features_at(series: pd.Series, origin: pd.Timestamp) -> pd.DataFrame` возвращает
одну строку с DatetimeIndex `[origin]`, столбцами в порядке:

| Столбец | Доступные данные |
| --- | --- |
| `lag_1` | count[t−1] |
| `lag_7` | count[t−7] |
| `rolling_7` | среднее count[t−7]…count[t−1] |
| `day_of_week` | день недели origin, Monday=0 |

Нужны семь предыдущих наблюдений. Самый ранний origin — восьмой день, самый
поздний — день после последнего наблюдения. Timestamp без timezone, полночь;
индекс ежедневный, возрастающий, уникальный, без пропусков, значения конечные и
неотрицательные. Нарушения — `ValueError`, без неявной интерполяции.
Изменение count[t:] и удаление всего будущего не меняют признаки t.
Сначала shift, потом rolling — target не входит в окно.

`run_study(output_dir: Path) -> Path` отказывает с `FileExistsError` для существующего
каталога и возвращает новый manifest.json. Сравните naive count[t−1], seasonal
count[t−7] и **одну существующую sklearn family Ridge**. Обучайте готовую sklearn
модель, не пишите ещё одну ручную regression. Гиперпараметры и train-only
preprocessing обоснуйте; на каждом origin обучающие targets строго раньше t.
Все три метода оцениваются на одинаковом упорядоченном наборе origins.

Отдельно проведите случайное разбиение допустимых origins с той же Ridge family
и сохраните фактические predictions. Это иллюстрация другой схемы оценки;
допустимы равные MAE и любой победитель. Разные test origins ограничивают прямое
сравнение; не объясняйте разность только leakage без анализа. Random split может
использовать более поздние targets для ранних test origins и не имитирует deployment.

## Сохранённый контракт

Создайте новый каталог с `data.json` (точные dataset_bytes), `split.json`,
`outputs.json`, `implementation.txt` (снимок вашего запускаемого кода), `report.md`
и `manifest.json`. Все JSON числа конечные, bool вместо чисел запрещён.

- `split.json`: `train_origins`, `test_origins` — непустые списки ISO `YYYY-MM-DD`.
  Их конкатенация — все даты начиная с восьмого дня, по порядку. Temporal test —
  сплошной хвост. `random_train_origins`, `random_test_origins` — другое непустое
  разбиение тех же допустимых дат, без повторов и пересечений.
- `outputs.json`: три identity поля (`run_id`, `dataset_sha256`, `split_sha256`),
  `origins` точно равен temporal test; `fit_origins` — объект test origin → список
  фактических дат training targets, каждая строго раньше данного origin.
  `predictions` — объект `naive`, `seasonal`, `model`, каждый список в порядке origins.
  `mae` — объект с теми же тремя ключами и MAE из **сохранённых** predictions.
  `random: {"origins": [...], "predictions": [...]}` содержит random test в порядке
  split; `comparison: {"random_mae": число, "temporal_mae": число}` пересчитывается
  из random predictions и temporal model. Не округляйте числа при сохранении.
- `manifest.json`: `schema_version: 1`, `exercise_id: "ml-forecasting-intro"`, непустой
  `run_id`, `dataset_sha256` (SHA-256 bytes data.json), `split_sha256` (bytes split.json),
  `config: {"horizon": 1, "model_family": "Ridge", ...}`, `review_status:
  "REQUIRES_REVIEW"`; `artifacts` — относительный путь → SHA-256 каждого файла,
  кроме самого manifest. Конфигурация содержит seed, параметры и preprocessing.
- `report.md`: цель, доступность признаков, split, общие origins, actual MAE трёх
  методов, random/temporal сравнение без навязанного победителя, ошибки и ограничения.

Validator проверяет сохранённые bytes и identities, исходные counts, chronology,
baseline predictions, общие score origins и заново считает MAE. Он не исполняет
сохранённый код и не загружает pickle. Списки fit_origins — проверяемые заявления,
не доказательство фактического fit: preprocessing, Ridge family и происхождение
predictions подтверждаются просмотром кода и ручным воспроизведением.

## Запуск и staged hints

Из корня, Windows/PyCharm, существующая `.venv`, CPU/offline:

```powershell
uv run --no-sync python scripts/learn.py test ml-forecasting-intro
uv run --no-sync python scripts/learn.py check ml-forecasting-intro
uv run --no-sync python -m modules.04_machine_learning.exercises.forecasting_intro.evidence C:/temp/my-forecast-run
```

1. Нарисуйте доступные даты для первого origin и вычислите lag/rolling вручную.
2. Вызовите features_at до и после порчи будущего; строки должны совпасть.
3. Постройте train rows через ту же функцию; перед fit проверяйте training target < t.
4. Сохраните predictions до подсчёта итоговой таблицы и перечитайте validator'ом.

## Критерий и уровни свидетельств

Unit: границы дат, future invariance, shift-before-rolling, арифметика MAE и
защита artifacts от подмены. Example: отдельная задача четырёх температур,
без реализации features_at, обучения или готового study. Smoke: student run
в новом tmp-каталоге с последующим readback. Evaluation: реальные сохранённые
Ridge/baseline/random predictions и MAE, а не факт прохождения инфраструктурных tests.
Review: объяснение split, признаки без утечки, preprocessing и интерпретация.
Искусственные zero predictions инфраструктурного fixture не являются ML-оценкой.

`test` допускает незаполненные TODO как xfail; `check` требует завершённых обязательных
tests без xfail/skip. Успех validator доказывает согласованность artifacts, но не
происхождение predictions; защита остаётся `REQUIRES_REVIEW`.
