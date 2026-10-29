# Градиенты MSE/BCE, L2 и точность вычислений

Обязательная практика · 90–120 минут · catalog ID `ml-gradient-derivations`.

## Перед началом

NumPy: формы и матричное умножение; производная суммы и правило цепочки. Пройдите [training bridge](../../07_training_bridge/README.md).

Полный вывод, ручной пример, ошибки и самостоятельный перенос находятся в
[theory.md](theory.md). Этот текст достаточен для работы без внешних курсов.
Начните с формул на бумаге, затем запустите [авторскую демонстрацию](demo.py).

## Ваша работа

Реализуйте `weighted_objective_gradient` в [starter.py](starter.py). Авторский пример использует одинаковые веса; ваша задача добавляет нормировку произвольных sample weights. Не импортируйте demo в starter.

Контракты форм, редукций, tie rules и ошибок описаны в theory. Меняйте только
starter; не заменяйте вызовы `exercise_call` и не снимайте проверки из тестов.
Сохраните собственную записку с расчетами, сравнением с библиотекой и ограничениями.
Не считайте выполнение авторского demo доказательством вашей реализации.

## Запуск из корня репозитория

Linux/WSL:

```bash
.venv/bin/python -m modules.04_machine_learning.exercises.gradient_derivations.demo
.venv/bin/python scripts/learn.py test ml-gradient-derivations
.venv/bin/python scripts/learn.py check ml-gradient-derivations
```

Windows/PyCharm Terminal:

```powershell
.venv/Scripts/python.exe -m modules.04_machine_learning.exercises.gradient_derivations.demo
.venv/Scripts/python.exe scripts/learn.py test ml-gradient-derivations
.venv/Scripts/python.exe scripts/learn.py check ml-gradient-derivations
```

`test` на нетронутом starter показывает ожидаемые xfail. Строгий `check` должен
завершиться ненулевым кодом, пока остались NotImplementedError, skip или xfail.
В catalog включен только `test_starter.py`: проход `test_demo.py` проверяет
материалы автора и не дает learner credit. Для прямого строгого запуска:

```bash
.venv/bin/python -m pytest -p roadmap_tools.strict_check modules/04_machine_learning/exercises/gradient_derivations/test_starter.py
```

Все примеры и тесты работают локально на CPU без сети и загрузки datasets.
При реализации пользуйтесь только установленными NumPy/sklearn, соблюдая
дополнительные ограничения конкретных функций в theory.

## Критерий завершения

Без подсказок выведите MSE/BCE по w и b, объясните коэффициенты n, 2 и lambda; предъявите finite differences и крайние логиты. Затем выполните независимый перенос из theory.

Строгие тесты должны пройти без skip/xfail. Дополнительно ревьюер оценивает
объяснение допущений, расчетов и независимого переноса по слабому/сильному ответу
в theory. Зеленые тесты не заменяют защиту и не подтверждают качество реальной
модели на новых данных. Следующий шаг — применить эти проверки в независимом
табличном проекте с происхождением данных и заранее выбранным split.
