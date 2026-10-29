# Стабильность обучения и условный paired bootstrap

Обязательная практика · 90–120 минут · catalog ID `data-training-stability`.

## Перед началом

[NumPy](../../01_numpy/README.md), train/validation/test, среднее и квантили. Сначала изучите [paired comparison](../paired_model_comparison/README.md).

Полный вывод, ручной пример, ошибки и самостоятельный перенос находятся в
[theory.md](theory.md). Этот текст достаточен для работы без внешних курсов.
Начните с формул на бумаге, затем запустите [авторскую демонстрацию](demo.py).

## Ваша работа

Реализуйте `classification_sweep` и `paired_accuracy_interval` в [starter.py](starter.py). Demo исследует регрессию и разницу losses; learner исследует accuracy классификации и получает явные resample indices.

Контракты форм, редукций, tie rules и ошибок описаны в theory. Меняйте только
starter; не заменяйте вызовы `exercise_call` и не снимайте проверки из тестов.
Сохраните собственную записку с расчетами, сравнением с библиотекой и ограничениями.
Не считайте выполнение авторского demo доказательством вашей реализации.

## Запуск из корня репозитория

Linux/WSL:

```bash
.venv/bin/python -m modules.03_data_foundations.exercises.training_stability.demo
.venv/bin/python scripts/learn.py test data-training-stability
.venv/bin/python scripts/learn.py check data-training-stability
```

Windows/PyCharm Terminal:

```powershell
.venv/Scripts/python.exe -m modules.03_data_foundations.exercises.training_stability.demo
.venv/Scripts/python.exe scripts/learn.py test data-training-stability
.venv/Scripts/python.exe scripts/learn.py check data-training-stability
```

`test` на нетронутом starter показывает ожидаемые xfail. Строгий `check` должен
завершиться ненулевым кодом, пока остались NotImplementedError, skip или xfail.
В catalog включен только `test_starter.py`: проход `test_demo.py` проверяет
материалы автора и не дает learner credit. Для прямого строгого запуска:

```bash
.venv/bin/python -m pytest -p roadmap_tools.strict_check modules/03_data_foundations/exercises/training_stability/test_starter.py
```

Все примеры и тесты работают локально на CPU без сети и загрузки datasets.
При реализации пользуйтесь только установленными NumPy/sklearn, соблюдая
дополнительные ограничения конкретных функций в theory.

## Критерий завершения

Предъявите seed×size таблицу с ID split и полными refit; отдельно paired interval фиксированных predictions. Объясните IID, group/time ограничения и что исключает locked holdout.

Строгие тесты должны пройти без skip/xfail. Дополнительно ревьюер оценивает
объяснение допущений, расчетов и независимого переноса по слабому/сильному ответу
в theory. Зеленые тесты не заменяют защиту и не подтверждают качество реальной
модели на новых данных. Следующий шаг — применить эти проверки в независимом
табличном проекте с происхождением данных и заранее выбранным split.
