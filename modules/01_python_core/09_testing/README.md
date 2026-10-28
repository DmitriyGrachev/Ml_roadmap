# Testing

## Goal

Write direct pytest checks with fixtures, parametrization, exception assertions, and focused mocks.

[Теория: от контракта к тестам, traceback и декомпозиция](theory.md) содержит
полный teacher example и отдельную намеренно сломанную демонстрацию. После
разбора напишите собственные тесты в [document outline practice](practice/document_outline/README.md),
проверьте изменение требования и AI-кандидата, затем вернитесь к существующим
`python-debug-mutable-defaults`, `python-review-stateful-report` и `python-mock-provider`.
Практика outline проверяется вручную: нового ID и progress нет; пустые тесты,
ожидаемая ошибка и зелёный teacher example не означают освоение.
Собственные тесты пишите в `outline_cases.py` и запускайте по явному пути из
практики: этот файл не входит в обычный автопоиск тестов урока `python-testing`.

## Java mental model

pytest covers a role similar to JUnit. Its fixture injection and plain `assert` style are conventions, not Java annotations and assertion APIs.

## Python model

Tests are functions discovered by name. Parametrization keeps one behavior readable across representative inputs; fixtures make setup explicit.

## Key concepts

Assert real outcomes and use mocks at external or slow boundaries. `pytest.raises` documents expected error behavior without swallowing unrelated failures.

## Example

Run `uv run python modules/01_python_core/09_testing/example.py` to see a currency rule whose cases fit naturally in a parametrized test.

Эта команда вызывает `main()` и печатает один результат, но не запускает тесты.
Чтобы выполнить три параметризованных случая из того же файла, из корня проекта:

```powershell
uv run pytest modules/01_python_core/09_testing/example.py -q
```

Явный путь нужен потому, что `example.py` не соответствует обычной маске
автопоиска файлов `test_*.py`. Успех этих демонстрационных тестов не засчитывает
самостоятельную работу `python-mock-provider`.

## Exercises

- [Test one provider interaction](exercises/mock_provider/README.md)

## Self-check

1. How does pytest discover a test?
2. When helps parametrization?
3. What is a fixture for?
4. When should a mock be used?
5. What does `pytest.raises` assert?

## Done when

You can choose a small behavior and express its expected outcome directly.
