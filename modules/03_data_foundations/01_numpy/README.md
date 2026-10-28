# NumPy arrays and vectorization

## Goal

Научиться предсказывать форму и значения результата, различать view/copy и оценивать
память до вычисления. Начните с [последовательного объяснения](theory.md):
§1–3 → §4–5 → §6–9. Это теория существующего `data-numpy`, не новый ID.

## Java mental model

Числовой NumPy array — не `List<Double>` и не Java `int[][]`: у него одна dtype и
прямоугольная shape. Обычный Java-массив массивов допускает строки разной длины.

## Python model

Сначала назовите смысл осей, затем dtype и форму, после — операцию. Совместимость
форм не гарантирует правильного смысла. Представление может разделять данные
с другим объектом массива: продолжение [Object Model](../../01_python_core/01_object_model/README.md).

## Key concepts

Shape, dtype, axis, indexing/masks, reshape, broadcasting, view/copy, vectorization
и ограничения памяти. Предпосылки: Python Collections, Functions и базовый Typing.

## Example

[walkthrough.py](walkthrough.py) пошагово разбирает измерения двух датчиков: формы,
выбор клеток, суммы, пороги, запись через view и оценку памяти. Сначала прогнозируйте
результат по [теории и схемам](theory.md), затем запускайте из корня проекта:

```powershell
uv run --offline --no-sync python modules/03_data_foundations/01_numpy/walkthrough.py
```

Существующий [example.py](example.py) сохранён: два SLA сравниваются с четырьмя
временами ответа, результат — булева матрица `(2, 4)`.

## Exercises

Сначала [Payment matrix](exercises/payment_matrix/README.md), `data-payment-matrix`:
формы, dtype, broadcasting, неизменность входа. Затем
[Image pooling](../exercises/image_pooling/README.md), `data-image-pooling`:
reshape, несколько осей и независимый результат. Условия и TODO не изменены.
Прогнозы indexing/dtype/memory в теории — самостоятельная устная/черновая проверка,
не новый автоматически зачтённый ID.

## Self-check

1. Чем shape, ndim, size и len отличаются для `(2, 3)`?
2. Как dtype влияет на дробные значения и память?
3. Почему `a[:, 1]` и `a[:, 1:2]` имеют разные формы?
4. Какую ось убирает `sum(axis=0)` и что меняет keepdims?
5. Почему `(2, 1)` совместима с `(2, 3)`, а `(2,)` — нет?
6. Как доказать, что срез разделяет память, а выбор списком индексов — нет?
7. Что гарантирует и чего не гарантирует vectorization?
8. Почему сумма nbytes всех представлений не равна памяти процесса?

## Done when

Вы прогнозируете новую вариацию до запуска и объясняете несовпадение, если оно было.
Собственная реализация проходит `check` выбранного задания; объяснение памяти и
индексации проверено человеком. Зелёные тесты teacher-примера не означают освоение.
