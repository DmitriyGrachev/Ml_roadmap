# MLflow и ограниченный поиск экспериментов

Независимая практика `ml-experiment-management`: реализуйте поиск настроек sklearn
на **train/dev**, сохраните реальные Optuna trials и MLflow runs, выберите модель
по проверяемой таблице validation и восстановите её локально. Новая предметная
область, исходные данные, функции в `starter.py` и защита — работа учащегося.
Авторский пример проверяет механизм библиотек; он не закрывает эту практику.

## Предварительные знания и результат

Нужны sklearn Pipeline, TF–IDF, логистическая регрессия, регуляризация, stratified/group
split, macro F1, JSON/SHA-256 и вводный [tracking_intro](../tracking_intro/README.md).
Сначала пройдите чистые протокольные тесты без дополнительных библиотек. Реальный
поиск требует группы `experiments` (MLflow 3.x + Optuna 5.0.0); sklearn уже входит
в базовые зависимости. Сервер MLflow, UI, облако и GPU не нужны.

```bash
uv sync --group experiments
uv run --group experiments pytest -q projects/document_intelligence_lab/experiment_management
```

Установка — отдельное явное действие с доступом к реестру пакетов. Import модулей и
обычный pytest ничего не скачивают и не запускают поиск. Без группы runtime выдаёт
`NOT_RUN` с инструкцией; это не успешный эксперимент. В обычном прогоне авторский
API test пропущен, незаполненные learner boundaries отмечены xfail. Для strict check
skip/xfail не являются выполнением.

## Trial, run и artifact

| Сущность | Что означает здесь | Что сохраняется |
|---|---|---|
| Optuna study | Одна заранее ограниченная процедура выбора | SQLite `study.sqlite`, seed sampler, direction |
| Trial | Одна предложенная конфигурация pipeline | Номер, params, state, dev value, run ID, dev predictions |
| MLflow run | Запись выполнения trial; идентичность не равна его номеру | Params, dev metric, теги provenance, `trial.json` |
| Logged model | Именованный набор сериализованных sklearn-байтов | Неизменяемый `model_id`, `models:/…`, source run ID |
| Artifact | Реальный файл, а не строка метрики | Trial JSON, sklearn flavor, подписи/requirements |

Один trial связан ровно с одним отдельным MLflow run через `user_attrs.run_id`.
Сохранённый лучший sklearn model связан с run выигравшего trial. Несколько файлов
внутри artifact не являются несколькими независимыми экспериментами.
Существующий `tracking_intro` уже умеет строить локальные SQLite/file URI,
проверять расположение artifacts и лениво импортировать MLflow с отключённой
телеметрией. Здесь переиспользуются только `local_store`,
`require_local_artifact_uri`, `_mlflow`; его `track_bundle`, авторские модели,
registry/promotion и готовый цикл поиска не используются как learner solution.

## Данные и вычисление objective

Сохраните `dataset.json`: объект с **ровно** ключами `train`, `dev`, `holdout`.
В каждом — 2..2000 строк, каждая с ровно четырьмя непустыми строковыми полями:

```json
{"id":"train-001","family":"contract-source-04","text":"...","label":"contract"}
```

`id` уникален глобально; `family` объединяет документы одного источника/шаблона.
Семейства и нормализованные тексты не пересекаются между split. Нормализация для
проверки дублей: Unicode casefold + схлопывание whitespace. У каждого split те же
не менее двух классов. Для собственной сдачи нужно не менее восьми train-строк,
новый домен и обоснованный split; маленький корпус — проверка протокола, не оценка
готовности к production. Не отправляйте приватные документы в репозиторий.

`protocol.objective_inputs` проверяет эти ограничения и возвращает **копии только
train/dev**. Learner `build_objective(train, dev, seed=...)` получает эти два списка;
holdout не передаётся. Внутри каждого trial:

1. Optuna предлагает `C` (конечное положительное число) и `word_ngram` (1 либо 2).
2. Создаётся новый `Pipeline([('tfidf', TfidfVectorizer(ngram_range=(1, word_ngram))),
   ('classifier', LogisticRegression(C=C, random_state=seed, max_iter=100))])`.
3. **Все** fit-операции, включая vocabulary/IDF, выполняются только на train.
4. Predict для dev сохраняется в исходном порядке, а значение objective вычисляется
   из labels и predictions. Вызов `trial.set_user_attr('dev_predictions', predictions)`
   обязателен. Возвращается числовой macro F1.

Для класса $c$: $F1_c = 2TP_c/(2TP_c+FP_c+FN_c)$; objective — среднее по классам dev.
В каждом split представлены все классы, поэтому знаменатель определён. Например,
для labels `[a,a,b,b]` и predictions `[a,a,a,b]` получаются $F1_a=4/5$,
$F1_b=2/3$, macro F1 $=11/15$. Это вычисленный пример формулы, не измерение качества
на реальном корпусе. Оптимизация — `direction='maximize'`; для loss понадобилось бы
`minimize`, что отдельно проверяется в задаче выбора.

Запустите `RandomSampler(seed=seed)`, `n_jobs=1`, заранее задайте целый `budget` от 1
до 4 (для независимой сдачи предпочтительно 4), сохраните persistent study в
`sqlite:///ABSOLUTE_PATH/study.sqlite`. Не дописывайте trials после просмотра
holdout. Одинаковая конфигурация, случайно предложенная дважды, тоже расходует бюджет.
Для ускорения этого урока вложенный CV не требуется.

## Learner boundaries

Все три функции `starter.py` намеренно содержат прямой `NotImplementedError`:

- `select_trial(trials, direction) -> int`: независимо реализуйте выбор только
  конечных `COMPLETE` trials, направление и tie break по меньшему номеру. При
  отсутствии кандидата/некорректном направлении/NaN — `ValueError`. `FAIL` и `PRUNED`
  не могут выиграть даже с привлекательным промежуточным значением.
- `build_objective(train, dev, *, seed) -> Callable`: реализуйте описанный выше
  sklearn objective. Не возвращайте константу и не подменяйте Optuna fixture-объектом.
- `run_search(dataset, output, *, seed=23, budget=4) -> Path`: самостоятельно
  свяжите actual Optuna, objective, MLflow, выбор, сохранение и reload; верните путь
  к новому каталогу. Existing output должен давать `FileExistsError`. При отсутствии
  runtime ошибка возникает до создания успешного report. Используйте свою функцию
  выбора; `protocol.select_best` — только аудиторский oracle, не решение learner.

Нельзя вызывать `demo.run_demo` или копировать его fixture в сдачу. Вспомогательные
`protocol`, `runtime` и `evidence` — scaffolding для валидации, они не реализуют
learner objective/search/logging. В частности `runtime.libraries()` импортирует SDK,
но не создаёт study/run и не выбирает модель.

## Контракт артефактов и реальная проверка

Выход — новый каталог внутри игнорируемого `artifacts/`, например
`artifacts/my-experiment-001/`. Не используйте входной каталог как output. Файлы:

| Путь | Содержание |
|---|---|
| `dataset.json` | Полный исходный train/dev/holdout JSON |
| `study.sqlite` | Реальное persistent Optuna study |
| `runs.sqlite` | MLflow SQLite store; никаких remote URI |
| `mlflow-artifacts/` | Локальные `trial.json` и выбранный sklearn flavor, не более 10 MB |
| `experiment.json` | Сводный контракт ниже + анализ учащегося |

У `experiment.json` обязательны:

- `schema_version: 1`, `exercise_id: 'ml-experiment-management'`,
  `evidence_kind: 'STUDENT_EXPERIMENT_MANAGEMENT'`, `code_sha256`: SHA-256 текущего
  `starter.py`; `quality_defense: 'REQUIRES_REVIEW'`.
- `dataset_sha256 = protocol.digest(dataset)`,
  `split_sha256 = protocol.split_digest(dataset)`. Canonical JSON: sorted keys,
  UTF-8, `ensure_ascii=False`, стандартные JSON separators, list order сохраняется.
- `objective: 'dev_macro_f1'`, `direction: 'maximize'`, целые `seed`, `budget`,
  `study_name`, `selected_trial`, `selected_run_id`, `trials` длины `budget`.
- Для **каждого** trial: `number`, `state` (`COMPLETE`/`FAIL`/`PRUNED`),
  `value` (для неуспешного обычно `null`), `params`, отдельный `run_id`,
  `dev_predictions` (для неуспешного можно `[]`), `fit_ids` ровно ordered train IDs,
  `dev_ids` ровно ordered dev IDs. Номера — `0..budget-1`.
- `dev_predictions` выбранного trial; `holdout_predictions` выбранной модели в
  порядке holdout; `holdout_macro_f1`, вычисленный из сохранённых predictions.
- `model_id` реального MLflow logged model, `model_uri: 'models:/<model_id>'`,
  `model_sha256 = runtime.model_digest(local_model_directory(...))`.
  В модели должны быть шаги `tfidf`/`classifier` из описанного pipeline.
- `versions` с реально импортированными `mlflow`, `optuna`, `sklearn`, `numpy`;
  `analysis` с непустыми строками `budget_bias`, `failure_pruning`, `holdout_policy`,
  `seed_limits`, `hf_transfer`. Для человека заполните [report-template.md](report-template.md).

Во **всех** MLflow runs логируйте params trial и теги `dataset_sha256`,
`split_sha256`, `trial_number`, `trial_state`, `objective`, `direction`, `seed`
(значения тегов — строки). Для COMPLETE логируется метрика `dev_macro_f1`, run
заканчивается `FINISHED`. Сохраните весь trial row через `mlflow.log_dict(row,
 'trial.json')`. В Optuna trial должны совпадать `value`, `params`, state,
`user_attrs.run_id`, `user_attrs.dev_predictions`. Неудачные trials тоже присутствуют
в таблице и store; один успешный trial обязателен, иначе успешного report нет.

Выберите лучшую модель по dev **до** единственного финального holdout evaluation.
Можно сохранить fitted модель выигравшего trial или заново fit на том же train
с теми же настройками/seed; объединять train+dev в этом контракте нельзя. Логируйте
sklearn flavor под выбранным run, с 1-D string tensor signature и явным
`pip_requirements`, чтобы SDK не пытался угадывать окружение. Для reload сначала
проверьте `get_logged_model(model_id).artifact_location`: URI должен находиться
в собственном `mlflow-artifacts/`. Helper `runtime.local_model_directory` делает
эту проверку. Сериализация sklearn использует pickle; разрешайте загрузку только
созданных вами локальных байтов.

`evidence.validate_experiment` независимо:

1. Проверяет identity, source/dataset/split digests и train/dev/holdout границы.
2. Пересчитывает dev values каждого COMPLETE trial и holdout metric из predictions;
   проверяет argmax validation table, состояния, tie break, selected run.
3. Читает реальные SQLite Optuna/MLflow через SDK, сравнивает params, values, state,
   per-trial artifacts и provenance. JSON с правдоподобными числами недостаточен.
4. Проверяет local artifact URI, model/source-run identity и SHA-256 всего flavor;
   загружает модель, воспроизводит dev/holdout predictions.
5. Клонирует выбранный pipeline, независимо обучает его на train и сравнивает
   vocabulary, IDF, classifier weights/intercept/classes. Это ловит fit на dev/holdout,
   даже если такой leakage не изменил итоговые классы predictions.

Верификатор не восстанавливает историю неучтённых попыток и не доказывает авторство;
проверяющий читает learner source, новый домен и защиту. Нет порога обязательного
роста метрики: на лёгком корпусе все trials могут дать одинаковый результат.

## Запуск учащегося и строгая сдача

Пример запуска после самостоятельной реализации:

```python
import json
from pathlib import Path
from projects.document_intelligence_lab.experiment_management.starter import run_search

source = json.loads(Path("my-documents.json").read_text(encoding="utf-8"))
run_search(source, Path("artifacts/my-experiment-001"), seed=23, budget=4)
```

```bash
ROADMAP_EXPERIMENT_EVIDENCE=artifacts/my-experiment-001 \
ROADMAP_EXPERIMENT_TRUST_LOCAL=1 \
uv run --group experiments python -m roadmap_tools check ml-experiment-management
```

`ROADMAP_EXPERIMENT_TRUST_LOCAL=1` — осознанное доверие собственному pickle,
не разрешение скачивать сторонний model. Completion targets — только
`test_starter.py`: независимый selector, actual objective и обязательный сохранённый
learner run с новым коротким rerun текущего `starter.run_search` на том же dataset
(`budget=2`). Без learner implementation и evidence strict completion не проходит.
Новый rerun — проверка работающего кода, не обязательный выигрыш по score.
Тест требует создать именно запрошенный новый output, отдельные SQLite stores и
новые run/model IDs; возврат старой папки не считается rerun. Повторный вызов с уже
существующим output обязан дать `FileExistsError`. В objective тест наблюдает реальные
sklearn `Pipeline.fit/predict`, порядок train/dev, применение `C`/`word_ngram` и
совпадение сохранённых predictions с выходами fitted pipeline. Копирование dev labels
и константный score без обучения не проходят; минимального значения метрики нет.

## Авторский механизм: отдельный явный smoke

```bash
uv run --group experiments python -m \
  projects.document_intelligence_lab.experiment_management.demo \
  --output artifacts/author-experiments-001
ROADMAP_RUN_EXPERIMENTS=1 uv run --group experiments pytest -q \
  projects/document_intelligence_lab/experiment_management/test_optional_api.py
```

Каждая команда явно делает только четыре tiny CPU trials на синтетических invoice/ticket
документах. Обычно выбирайте одну из команд. Тест дополнительно запрещает sockets,
проверяет saved/reloaded predictions и отклоняет подменённую метрику в реальном
MLflow store. Он не является completion target и не выдаёт learner credit.

## Выбор бюджета, seed, leakage и перенос

Чем больше configurations сравниваются на одном dev, тем вероятнее случайно выбрать
модель, подогнанную под шум validation. Бюджет и правила tie break фиксируются **до**
поиска. Сравнивать два поиска только по лучшему score нечестно при разных budgets,
разных split, числах seed или просмотренной вручную history. При достаточных данных
nested CV отделяет внутренний выбор hyperparameters от внешней оценки: inner folds
выбирают параметры, outer folds оценивают всю процедуру выбора. Это дороже; финальный
holdout остаётся инструментом независимой проверки при заранее закреплённой процедуре.

Seed фиксирует последовательность предложений sampler и контролируемую случайность
оценщика. Он не исправляет leakage, неверные labels, выбор удобного split, переобучение
на dev, версии библиотек, порядок данных или аппаратную недетерминированность.
Parallel Optuna и adaptive sampler могут зависеть от порядка завершения trials:
поэтому здесь `n_jobs=1`, фиксированные data/split digests и версии.

Pruning — раннее завершение по промежуточному сигналу, не готовый финальный dev score.
`PRUNED`/`FAIL` остаются в журнале и расходуют бюджет; ошибка не превращается в
`COMPLETE` с нулём. Не сравнивайте промежуточный loss с финальным macro F1. Запишите
причину failure/pruning и условия повторного запуска. В smoke нет обязательного
искусственного падения; отдельные adversarial tests проверяют невозможность такого выбора.

В HF Trainer/SFT сохраняются те же понятия: trial configuration → отдельный training
run → checkpoints/tokenizer/config artifacts → evaluation protocol. К `seed` и split
hash добавляются revision локального model snapshot, tokenizer/template revision,
optimizer/scheduler, effective batch, checkpoint choice и target mask. SFT prompt tokens
нельзя включать в supervised loss, а dev/holdout ответы — в обучение. Промежуточный
checkpoint, chosen epoch и adapter — часть выбора, которую надо учитывать в бюджете.
Этот sklearn урок не запускает HF/SFT обучение и не доказывает качество pretrained модели.

## Типичные ошибки и защита человеком

| Ошибка | Следствие | Проверка/объяснение |
|---|---|---|
| `study(direction='minimize')` для F1 | Выбрана худшая модель | Selector tests + сверка real study direction |
| `fit_transform` на train+dev | Vocabulary/IDF знают validation | Независимый train-only refit |
| Один family в нескольких split | Почти одинаковые документы с обеих сторон | Проверка family/text overlap |
| Улучшение holdout через новые trials | Независимая оценка потеряна | История trials, source review, защита |
| Параметры в JSON отличаются от модели | Эксперимент невозможно повторить | MLflow/Optuna/selected-pipeline reconciliation |
| Сохранены только лучшие цифры | Скрыты budget и failures | Все budget trials, разные run IDs |
| Авторский fixture переименован в learner | Нет независимой практики | Evidence kind, source hash, новый домен, review |

Проверяющий выбирает другой маленький seed/budget для ручного rerun, просит показать
selected trial/run/model ID, открыть `trial.json`, пересчитать одну строку macro F1
и объяснить, почему другой trial не выиграл. Учащийся показывает отсутствие holdout
в objective, признаёт ограничения seed/корпуса, объясняет nested CV и перенос в
HF/SFT. Сохраните human rerun command, проверенные IDs, результат и дату в отчёте;
`REQUIRES_REVIEW` не заменяется автогенерированным `PASSED`.
