# Доставка src-layout пакета и единый preprocessing

Catalog ID: `python-package-delivery`.

Предпосылки: функции, import, пути, тесты, JSON.
Прочитайте [теорию](theory.md), затем сравните два независимых проекта:
[авторский parcel-features](example_project/pyproject.toml) и
[учебный ticket-features](student_project/pyproject.toml).

## Авторский маршрут

[demo.py](demo.py) собирает настоящий wheel установленным `uv_build`, создаёт
временный venv, устанавливает локальный wheel без сети и запускает пакет из другого
каталога. Внутри [transform.py](example_project/src/parcel_features/transform.py)
определён один контракт; `train.py` и `serve.py` используют одну реализацию.
`__main__.py` позволяет вызвать пакет как `python -m parcel_features`.

Подготовка инструментов допускает сеть; сама проверка работает без неё:

```bash
uv sync
uv run --offline python -m modules.01_python_core.exercises.package_delivery.demo
uv run --offline pytest modules/01_python_core/exercises/package_delivery/test_demo.py -q
```

Ожидаемые features: train `[[2.5, 8.0], [0.0, 4.0]]`, serve `[2.5, 8.0]`.
Новый venv получает pip из локального `ensurepip`, устанавливается только готовый
wheel с `--no-index --no-deps`. Исходное окружение должно содержать uv_build;
если Python собран без ensurepip, сначала используйте полноценный Python 3.12+.
Никаких wheel, venv или `dist` не нужно сохранять в репозитории.

## Самостоятельная поставка

Реализуйте `deliver(project_dir, work_dir)` в [starter.py](starter.py): соберите
**переданный** проект, установите wheel в новое окружение под `work_dir` и верните
`Path` его Python. Установку editable и внедрение исходного пути не используйте.
Установка выполняется без сети. Можно изучить технические приёмы автора, но
нельзя вернуть его Python или поставить parcel-features вместо ticket-features.

Внутри `student_project/src/ticket_features` заполните три границы:
`transform.transform`, `train.training_matrix`, `serve.serving_vector`.
Контракт для одного ticket:

- `duration_minutes`: конечное неотрицательное `int`/`float`; `bool` недопустим.
- `priority`: строка; после `strip().casefold()` одно из `low`, `normal`, `urgent`.
- Выход: `[min(duration_minutes, 120) / 120, priority_code]`, где коды равны
  `0.0`, `1.0`, `2.0` соответственно. Неизвестный priority и некорректная duration
  дают `ValueError`. Все значения результата — числа с плавающей точкой.
- `training_matrix` сохраняет порядок и возвращает `[]` для пустого входа;
  `serving_vector` даёт ровно тот же вектор для той же записи. Вход не изменяется.
  Обе стороны используют одну реализацию преобразования.

Готовый `__main__.py` не содержит ответа на задание: он станет исполняемым после
реализации функций. Tests запускают **установленный** пакет и неизвестные заранее
записи, проверяют `__file__`, venv, Unicode в авторском примере и ошибки в learner API.

```bash
uv run --offline pytest modules/01_python_core/exercises/package_delivery/test_starter.py -q
uv run --offline python -m roadmap_tools.cli check python-package-delivery
```

Исходный starter ожидаемо `xfail`; строгая проверка не даёт за это зачёт.
Ручная установка из исходников без clean-env проверки не завершает упражнение.

## Защита и перенос

Слабое доказательство: успешный `import` из корня проекта. Сильное: путь wheel,
команда установки без индекса, запуск `-I -m` из внешнего каталога и точные feature
values на новой записи. Покажите, где проверяется, что import идёт из нового venv.
Объясните разницу между build requirements и runtime dependencies.

Перенос: добавьте в мысленную схему обучаемый scaler и model artifact. Где выполняется
`fit`, какие файлы войдут в поставку, как проверите несовместимость feature order
при загрузке старой модели? Предложите негативный тест, который сломается при
разных единицах измерения у train и serve. Реальный cloud/PyPI publish не требуется.
