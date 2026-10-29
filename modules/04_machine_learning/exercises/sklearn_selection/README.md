# sklearn: выбор pipeline и permutation importance

ID: `ml-sklearn-selection`. Сложность: средняя; 90–120 минут.

## Перед началом

Нужны [preprocessing](../../03_preprocessing/README.md),
[групповая валидация](../../02_validation/README.md),
[оценка классификации](../../05_evaluation/README.md) и
[воспроизводимость](../../06_reproducibility/README.md).
В [theory.md](theory.md) разобраны схема fold, ручной расчёт macro-F1, утечки
и пределы интерпретации. Это расширение готовой фабрики preprocessing:
здесь вы выбираете параметр по CV и отдельно объясняете frozen-модель на holdout.

## Задание

Меняйте только [starter.py](starter.py). `select_pipeline(frame, labels, groups,
*, seed)` получает **только train**. Frame непустой, с уникальными строковыми
именами колонок; содержит хотя бы один числовой и один категориальный признак.
Числовые колонки — integer/float, категориальные — object/string/category со
строками и пропусками (`np.nan`). Остальные dtype отклоняются. `labels/groups`
— одномерные массивы по одной позиции на строку, не join по индексу DataFrame.
Метки — целочисленные бинарные 0/1 с обоими классами. Группы непотерянные,
целочисленные ID, минимум три различные группы; каждый training fold должен содержать
оба класса. NaN в признаках разрешены, бесконечности — нет. Ошибки контракта
дают `ValueError`. Не меняйте входы. `seed` задаёт `random_state` модели.

Верните `(fitted_pipeline, cv_table)`:

- `Pipeline` с шагами `preprocess` и `model`. `preprocess` — `ColumnTransformer`
  с ветвями `num` и `cat`, сохранением исходного порядка колонок в каждой ветви
  и `remainder='drop'`. В `num`: `imputer=SimpleImputer(strategy='median',
  keep_empty_features=True)` и `scaler=StandardScaler()`. В `cat`:
  `imputer=SimpleImputer(strategy='constant', fill_value='__missing__',
  keep_empty_features=True)` и `encoder=OneHotEncoder(handle_unknown='ignore')`.
  Полностью пустой numeric-признак сохраняется с заполнением нулём.
- `model=LogisticRegression(solver='lbfgs', max_iter=200, random_state=seed)`.
  Подберите **только** `C` из `(0.1, 1.0, 10.0)`. Используйте
  `GroupKFold(n_splits=3, shuffle=False)` и `f1_macro`, три складки для каждого C.
  Pipeline создаёт и обучает preprocessing заново внутри каждой складки.
  `n_jobs=1`, ошибка обучения должна завершать запуск (`error_score='raise'`),
  если используете `GridSearchCV`. При равном среднем score выбирайте меньший C.
  После выбора refit выполняется один раз на всём переданном train.
- `cv_table` — новый DataFrame с RangeIndex, три строки в порядке возрастания C,
  колонки строго `C, split0_test_score, split1_test_score, split2_test_score,
  mean_test_score, rank_test_score`. Score — `float64`, rank — целое с минимальным
  рангом при равенстве (`1, 1, 3`); больше score — лучше. Складки должны
  соответствовать именно указанному `GroupKFold`, без пользовательского shuffle.

`permutation_report(model, x_holdout, y_holdout, *, seed)` получает уже fitted
pipeline и отдельный holdout с теми же признаками. Не делает `fit`, подбор C
или выбор признаков. Используйте `permutation_importance(scoring='f1_macro',
n_repeats=5, random_state=seed, n_jobs=1)`. Верните DataFrame с RangeIndex и
колонками `feature, importance_mean, importance_std` в исходном порядке колонок
holdout; одна строка на **исходный** признак, до one-hot. std — популяционное
отклонение пяти изменений score. Отрицательные importance не обрезайте.
Frame, labels, модель и обученные статистики после report сохраняются.
Holdout не является аргументом `select_pipeline` и не участвует в CV.

## Проверка

Из корня репозитория:

```bash
.venv/bin/python -m modules.04_machine_learning.exercises.sklearn_selection.example
.venv/bin/python -m pytest modules/04_machine_learning/exercises/sklearn_selection -q
.venv/bin/python scripts/learn.py test ml-sklearn-selection
.venv/bin/python scripts/learn.py check ml-sklearn-selection
```

На Windows используйте `.venv/Scripts/python.exe`. [example.py](example.py)
обучает одну модель на восьми фиксированных строках и предсказывает две другие.
Это bounded CPU пример трансформации неизвестной категории; он не выполняет
подбор C или permutation importance и не является исследованием качества.
Импорт ничего не обучает, pytest не использует сеть и загрузки. Дополнительных
зависимостей и артефактов не требуется; данные только синтетические.

Learner completion требует обе функции `starter.py` и только `test_starter.py`;
`test_example.py` проверяет авторский разбор. Непройденные TODO дают ожидаемые
xfail при `test`; строгий `check` отвергает xfail/skip. Авторский smoke не даёт
credit. Тесты проверяют все CV fold score независимым расчётом, fit имьютеров
внутри складок, перемешанные labels, незнакомые категории и неизменность holdout.

## Критерии переноса

Объясните выбор group ID для нового домена, покажите сохранение обоих классов
в каждом training fold, разберите отрицательную importance и два коррелирующих
признака. Человек оценивает правдоподобие split и выводов. Автоматические
проверки не доказывают, что ваша production-группа выбрана корректно, и не
дают оснований публиковать качество на реальных данных. SHAP не требуется.
