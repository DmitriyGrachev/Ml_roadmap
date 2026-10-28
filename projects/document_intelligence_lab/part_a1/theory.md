# Почему «у меня работает» ещё не воспроизведение

Вы переносите классификатор документов на другой компьютер. Модель сохранили,
но vectorizer пересоздали, порядок labels поменяли, а метрики взяли из старого run.
Получится ли тот же эксперимент? До чтения предскажите, какое из трёх изменений
может не вызвать исключения, но изменить смысл ответа.

Интуиция: переносить нужно целый рецепт вместе с его зафиксированными ингредиентами.
Данные, partition, fitted preprocessing и модель образуют одну проверяемую связь.
Рецепт помогает повторить приготовление, но не доказывает, что блюдо понравится
новому гостю: воспроизведение не означает обобщение на иной домен.

Нужные вычисления уже разобраны в [NumPy](../../../modules/03_data_foundations/01_numpy/README.md),
[validation](../../../modules/04_machine_learning/02_validation/README.md),
[preprocessing](../../../modules/04_machine_learning/03_preprocessing/README.md),
[метриках и uncertainty](../../../modules/04_machine_learning/05_evaluation/README.md).
Здесь новое умение — связать данные, код, решение и реальные сохранённые bytes.

## Точные слова после интуиции

Dataset identity — digest точных bytes data.json, split identity — digest splits.json.
Content fingerprint отдельно связывает одну запись с UTF-8 bytes её текста.
Group — наблюдения одного семейства, которые нельзя делить между выборками.
Run ID различает исполнения; manifest digest различает конкретные bundles.
Fitted preprocessing содержит выученные значения (например IDF), а configuration
только описывает настройки. Pipeline сохраняет fitted vectorizer с classifier.
Integrity означает совпадение bytes; trust — сознательное решение оператора об авторе.

В A1 raw boundary — только тексты. Ground truth и ID нужны evaluation, но не inference.
Labels — canonical строки; integer class ID другой модели потребует явного mapping.
Подробные поля и функции находятся в [контракте](schema.md).

```text
data + sources + fixed splits → проверка IDs / groups / hashes
                                           |
code + seed + fixed candidates ─────────→ run_demo
                                           |
                           train: fit TF-IDF + linear model
                                           |
                           validation: зафиксировать выбор
                                           |
                              test: один общий cohort
                                           |
              NEW bundles: model / predictions / metrics / errors / timing
                                           |
                      перенос каталога → новый процесс → replay
```

Текстовая альтернатива: код проверяет data/sources/splits, fit читает только train,
validation фиксирует выбор, затем test создаёт predictions. Writer вычисляет metrics
и errors, записывает manifest с hashes. Loader проверяет bytes и повторяет predictions.
Время fit/inference измеряется во время run; diagram не обещает качество модели.

## Маленький run с конкретными числами

Teacher [demo.py](demo.py) читает 21 авторское описание фигуры, три labels.
Сначала [сверьте происхождение и спорные аннотации](fixtures/annotation-guide.md).
Train = 12, validation = 3, test = 6. Базовые rules знают `circle` и `square`,
а fallback = `circle`: предскажите, что произойдёт с `small blue triangle object`.

TF-IDF + LogisticRegression получает все три labels только из train.
Для токена `object`: N = 12 документов, document frequency = 6;
smoothed IDF = ln((1+12)/(1+6))+1 ≈ 1.619. Это fitted значение хранится в Pipeline.
Если ошибочно fit на всех 21 документах, получится другой IDF; тест проверяет этот дефект.
Цвет/размер сами по себе не задают label. Оба кандидата фиксированы до evaluation;
выбираем по validation macro F1, tie — имя метода. На этой fixture выигрывает TF-IDF.

Предсказания rules на test:

| row_id | Истина | Prediction | Что произошло |
| --- | --- | --- | --- |
| s16 | circle | circle | Найден token circle |
| s17 | square | square | Найден token square |
| s18 | triangle | circle | Не найдено rule, использован fallback |
| s19 | circle | circle | Найден token circle |
| s20 | square | square | Найден token square |
| s21 | triangle | circle | Та же незакрытая категория |

Confusion matrix, строки — истина, столбцы — prediction, порядок circle/square/triangle:

| True \ predicted | circle | square | triangle |
| --- | ---: | ---: | ---: |
| circle | 2 | 0 | 0 |
| square | 0 | 2 | 0 |
| triangle | 2 | 0 | 0 |

Accuracy = (2+2+0)/6 = 2/3. Для circle precision = 2/4, recall = 2/2,
F1 = 2·2/(4+2) = 2/3. Square F1 = 1. Triangle F1 = 0 при zero-division=0.
Macro F1 = (2/3+1+0)/3 = 5/9 ≈ 0.556. Если удалить отсутствующий predicted class
triangle из усреднения, число станет неверным. Полный label universe задан data.
TF-IDF здесь даёт все шесть правильных answers; это лексически простой synthetic smoke.

Карточка ошибки s18: текст `small blue triangle object`, truth triangle, prediction
circle, автоматическая category `misclassification`. Человек уточняет причину:
fallback закрывает неизвестный shape неверным известным классом. s21 подтверждает
повтор того же ограничения. Автоматический error list не подменяет такой разбор.

## Ошибка, которая может выглядеть убедительно

Изменили model.pkl, а predictions/metrics оставили прежними. Даже пересчитанный
hash нового model не спасает: loader делает actual inference и отклоняет несогласие.
Перестановка ID тоже запрещена — список должен быть ровно в порядке fixed test.
Переписанный report с правильными hashes не становится доказательством честного опыта:
provenance, способ выбора и объяснение результата требуют защиты.

Pickle может исполнить код до получения модели. Hash отвечает «те ли это bytes?»;
решение доверять локальному producer принимает оператор заранее. Он задаёт directory,
expected manifest digest и explicit trusted flag до старта сервиса. Пользователь
inference отправляет только text. У safe JSON rules исполняемой serialization нет.

CPU timing — wall-clock seconds с sample count, batch, cold/warm и device.
Peak memory не измеряли, поэтому `null` и конкретная причина. Размер model.pkl
на диске не равен RAM. Два запуска могут иметь одинаковые predictions и разные timings.
На шести synthetic строках score 1 не оценивает новый язык, OCR, шаблон или класс.

## Проверка понимания и независимый перенос

1. Что изменится в identity, если переформатировать JSON без изменения текста?
2. Почему source_id и group_id выполняют разные роли? Что нарушит перенос партии в test?
3. Какие значения matrix изменятся, если s18 станет верным triangle? Пересчитайте macro F1.
4. Почему повторный fit vectorizer при reload меняет эксперимент даже при том же model code?
5. Почему правильный manifest digest не разрешает загрузить чужой pickle?
6. Что из integrity, воспроизведения, generalization и самостоятельности доказывает зелёный test?
7. Как оценивать библиотечные notices, если новое требование запрещает путать access и event?

<details>
<summary>Проверка расчёта вопроса 3 после своей попытки</summary>

Triangle row станет `[1,0,1]`. Circle F1 = 4/5, square = 1, triangle = 2/3;
macro F1 = (4/5+1+2/3)/3 = 37/45 ≈ 0.822. Accuracy = 5/6.

</details>

[Самостоятельное задание](exercise/README.md) использует другие labels и notices;
готового learner report или pipeline здесь нет. [CI](../../../docs/continuous-integration.md)
проверяет инфраструктуру и teacher mechanics. Strict exercise check отклоняет TODO;
даже его успешный выход оставляет содержательную защиту `REQUIRES_REVIEW`.

Источники для остановки: локальные главы validation/preprocessing/evaluation выше,
[общие проверки hashes](../../../src/roadmap_tools/experiment_evidence.py) и
[schema A1](schema.md). Достаточно объяснить один run и перенести bundle; заново
изучать калибровку, писать split алгоритм или скачивать pretrained model не требуется.
Материал проверяется локальным offline запуском; внешний benchmark и live inference
здесь `NOT_RUN`. Структурные проверки Markdown не равны визуальному просмотру.
