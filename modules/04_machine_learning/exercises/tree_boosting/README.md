# Перебор порогов и остаточный бустинг

Обязательная практика · 90–120 минут · catalog ID `ml-tree-boosting`.

## Перед началом

[Базовые модели](../../04_models/README.md), среднее/дисперсия, [разделение данных](../../02_validation/README.md). Если ссылка на тему не знакома, сначала прочтите ее.

Полный вывод, ручной пример, ошибки и самостоятельный перенос находятся в
[theory.md](theory.md). Этот текст достаточен для работы без внешних курсов.
Начните с формул на бумаге, затем запустите [авторскую демонстрацию](demo.py).

## Ваша работа

Реализуйте `best_gini_split` и `boost_predict` в [starter.py](starter.py). Demo показывает regression SSE; ученик строит классификационный splitter и прогноз для новых query выбранным ансамблем.

Контракты форм, редукций, tie rules и ошибок описаны в theory. Меняйте только
starter; не заменяйте вызовы `exercise_call` и не снимайте проверки из тестов.
Сохраните собственную записку с расчетами, сравнением с библиотекой и ограничениями.
Не считайте выполнение авторского demo доказательством вашей реализации.

## Запуск из корня репозитория

Linux/WSL:

```bash
.venv/bin/python -m modules.04_machine_learning.exercises.tree_boosting.demo
.venv/bin/python scripts/learn.py test ml-tree-boosting
.venv/bin/python scripts/learn.py check ml-tree-boosting
```

Windows/PyCharm Terminal:

```powershell
.venv/Scripts/python.exe -m modules.04_machine_learning.exercises.tree_boosting.demo
.venv/Scripts/python.exe scripts/learn.py test ml-tree-boosting
.venv/Scripts/python.exe scripts/learn.py check ml-tree-boosting
```

`test` на нетронутом starter показывает ожидаемые xfail. Строгий `check` должен
завершиться ненулевым кодом, пока остались NotImplementedError, skip или xfail.
В catalog включен только `test_starter.py`: проход `test_demo.py` проверяет
материалы автора и не дает learner credit. Для прямого строгого запуска:

```bash
.venv/bin/python -m pytest -p roadmap_tools.strict_check modules/04_machine_learning/exercises/tree_boosting/test_starter.py
```

Все примеры и тесты работают локально на CPU без сети и загрузки datasets.
При реализации пользуйтесь только установленными NumPy/sklearn, соблюдая
дополнительные ограничения конкретных функций в theory.

## Критерий завершения

Выпишите все кандидаты, посчитайте Gini/SSE и три шага residual update. Покажите validation, где правильный selected_step равен 0, и объясните судьбу test.

Строгие тесты должны пройти без skip/xfail. Дополнительно ревьюер оценивает
объяснение допущений, расчетов и независимого переноса по слабому/сильному ответу
в theory. Зеленые тесты не заменяют защиту и не подтверждают качество реальной
модели на новых данных. Следующий шаг — применить эти проверки в независимом
табличном проекте с происхождением данных и заранее выбранным split.
