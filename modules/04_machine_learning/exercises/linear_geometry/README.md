# Геометрия линейной модели: ранг, Ridge, PCA

Обязательная практика · 90–120 минут · catalog ID `ml-linear-geometry`.

## Перед началом

Матрицы, скалярное произведение и [NumPy](../../../03_data_foundations/01_numpy/README.md); [preprocessing без утечки](../../03_preprocessing/README.md).

Полный вывод, ручной пример, ошибки и самостоятельный перенос находятся в
[theory.md](theory.md). Этот текст достаточен для работы без внешних курсов.
Начните с формул на бумаге, затем запустите [авторскую демонстрацию](demo.py).

## Ваша работа

Реализуйте `centered_ridge` и `principal_components` в [starter.py](starter.py) для произвольной нецентрированной матрицы. В demo разобраны фиксированные матрицы; решение задачи должно переноситься на другие формы и масштабы.

Контракты форм, редукций, tie rules и ошибок описаны в theory. Меняйте только
starter; не заменяйте вызовы `exercise_call` и не снимайте проверки из тестов.
Сохраните собственную записку с расчетами, сравнением с библиотекой и ограничениями.
Не считайте выполнение авторского demo доказательством вашей реализации.

## Запуск из корня репозитория

Linux/WSL:

```bash
.venv/bin/python -m modules.04_machine_learning.exercises.linear_geometry.demo
.venv/bin/python scripts/learn.py test ml-linear-geometry
.venv/bin/python scripts/learn.py check ml-linear-geometry
```

Windows/PyCharm Terminal:

```powershell
.venv/Scripts/python.exe -m modules.04_machine_learning.exercises.linear_geometry.demo
.venv/Scripts/python.exe scripts/learn.py test ml-linear-geometry
.venv/Scripts/python.exe scripts/learn.py check ml-linear-geometry
```

`test` на нетронутом starter показывает ожидаемые xfail. Строгий `check` должен
завершиться ненулевым кодом, пока остались NotImplementedError, skip или xfail.
В catalog включен только `test_starter.py`: проход `test_demo.py` проверяет
материалы автора и не дает learner credit. Для прямого строгого запуска:

```bash
.venv/bin/python -m pytest -p roadmap_tools.strict_check modules/04_machine_learning/exercises/linear_geometry/test_starter.py
```

Все примеры и тесты работают локально на CPU без сети и загрузки datasets.
При реализации пользуйтесь только установленными NumPy/sklearn, соблюдая
дополнительные ограничения конкретных функций в theory.

## Критерий завершения

Назовите null space и объясните condition number; решите covariance 2×2 вручную, согласуйте alpha с выбранной редукцией и защитите сравнение eigenvectors по подпространству.

Строгие тесты должны пройти без skip/xfail. Дополнительно ревьюер оценивает
объяснение допущений, расчетов и независимого переноса по слабому/сильному ответу
в theory. Зеленые тесты не заменяют защиту и не подтверждают качество реальной
модели на новых данных. Следующий шаг — применить эти проверки в независимом
табличном проекте с происхождением данных и заранее выбранным split.
