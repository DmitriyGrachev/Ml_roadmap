# Продолжение той же траектории обучения

ID: `lab-training-resume`. Prerequisite: [lab-pytorch](../../README.md).
CPU, offline, опциональное training-окружение. Это отдельный зачёт после лабораторной.

## Задача

Inference загружает веса для прогнозов. Restart начинает новый запуск. Resume
продолжает ту же последовательность обновлений, включая momentum и случайность.
Сравните 7 непрерывных шагов с остановкой после 3 шагов и продолжением до 7
в новом процессе. Отдельно проверьте остановку после 4 шагов — на границе эпохи.
Численная воспроизводимость здесь ограничена тем же CPU, версиями Python/NumPy/Torch
и окружением; между устройствами и версиями побитовое совпадение не обещается.

Меняйте `starter.py`: функции `capture_state` и `restore_state`. `fixture.py`,
`evidence.py`, тесты и `TrainingCursor` задают контракт. Собственный драйвер и
объяснение можно добавить отдельно. Старые TODO лабораторной решать заново не нужно.

## Контракт

`capture_state(model, optimizer, cursor, identity) -> dict[str, object]` вызывается
после `optimizer.step()`. Верните независимый снимок: будущие обновления модели
не должны менять сохранённый словарь. Ключи: `model` (state_dict), `optimizer`
(state_dict), `cursor` (простой словарь полей TrainingCursor), `identity`
(копия предоставленного mapping), `rng` (ровно `python`, `numpy`, `torch`).
Содержимое допускает только тензоры и простые Python значения; никакие экземпляры
модулей, optimizer, dataclass или NumPy ndarray в checkpoint не допустимы.

`restore_state(model, optimizer, state, identity) -> TrainingCursor` проверяет
полноту, совместимость модели, совпадение config/data/split identity и допустимость
курсора, восстанавливает модель, SGD momentum и использованные генераторы.
Неполное/несовместимое состояние, неверная identity или курсор дают `ValueError`.
Порядок RNG восстановления должен учитывать случайность при создании новой модели.

Используются глобальные `random`, legacy `np.random` и CPU Torch RNG.
Python влияет на shuffle и масштаб признаков, NumPy — на шум, Torch — на dropout.
Состояние `default_rng`/PCG64 здесь не заменяет состояние `np.random`/MT19937.
Продумайте безопасное представление NumPy state: числовой массив надо кодировать
примитивами или тензором и восстанавливать исходный dtype. `weights_only=True`
не разрешает произвольное распаковывание классов; checksum этого не меняет.
DataLoader использует отдельный локальный generator только для служебного seed
итератора; он пересоздаётся детерминированно и не влияет на обучение. Его отсутствие
в checkpoint не теряет используемую случайность. Это проверяет infrastructure test.
См. [документацию PyTorch о генераторе DataLoader](https://docs.pytorch.org/docs/2.14/data.html#randomness-in-multi-process-data-loading).

Fixture: 10 train и 2 validation строки, сеть 4→6→2 с dropout 0.25, SGD lr=0.03,
momentum=0.8, batch_size=3, num_workers=0. Тренировочные ID — `object-00`…`object-09`.
`sample_order` — полная перестановка train ID текущей эпохи; `next_batch_offset`
указывает следующую строку этого порядка. В эпохе батчи 3,3,3,1; после последнего
шага курсор остаётся с offset=10, а новая перестановка создаётся при следующем шаге.
Допустимые offset после шага: 3,6,9,10 (также 0 для начала); global_step должен
совпадать с epoch и числом уже обработанных батчей. Повтор предыдущего батча
недопустим. После шага 3: epoch=0/offset=9; после 4: epoch=0/offset=10;
после 7: epoch=1/offset=9. Scheduler не используется.

## Запуск из корня репозитория

```powershell
.venv-training/Scripts/python.exe scripts/learn.py test lab-training-resume
.venv-training/Scripts/python.exe scripts/learn.py check lab-training-resume
.venv-training/Scripts/python.exe -m pytest labs/01_pytorch_foundations/exercises/resume_training -q
```

При обычном setup можно использовать `uv run --group training python` вместо
пути к Python. В PyCharm выберите training-интерпретатор и working directory корня.
Числовые имена пакетов запускайте через `-m` или `importlib`, не через обычный import.
Base-окружение корректно сообщает отсутствие optional training; оно не даёт зачёт.
`test` допускает незавершённые TODO как xfail, `check` отклоняет xfail/skip.

`fixture.new_run()` создаёт запуск; `advance(..., until=3)` возвращает курсор и trace.
После собственной реализации capture сохраните checkpoint через `save_checkpoint`.
`fresh_run(output, checkpoint=path)` запускает другой Python-процесс, с другим
начальным seed, и вызывает вашу `restore_state`. Без checkpoint он исполняет baseline.
Все output пути должны быть новыми: harness не перезаписывает артефакты.

## Артефакты и проверка

Создайте свои файлы в `generated-reports/training-resume/`: `continuous.pt` и
`resumed.pt` с двумя полными traces, настоящий `checkpoint.pt` после шага 3,
`snapshot.json`, `split.json`, `manifest.json`. Продолженный trace включает prefix
первых трёх шагов и suffix из нового процесса. Формат наблюдений задаёт `fixture.result`:
trace содержит epoch/global_step/IDs/loss, итоговые model/optimizer/cursor/identity,
validation inference и следующие три RNG draw. RNG draw — наблюдение, не состояние.
Снимок и split сохраните байтами `fixture.canonical_bytes(SNAPSHOT/SPLIT)`.

Manifest: `schema_version=1`, `exercise_id="lab-training-resume"`,
`dataset_sha256`/`split_sha256` фактических файлов, `config=fixture.CONFIG`,
`artifacts` — mapping имён трёх `.pt` файлов на SHA-256 их байтов,
`review_status="REQUIRES_REVIEW"`, `explanation` — ваше содержательное объяснение
resume/inference/restart, границы батча и ограничения воспроизводимости.
Значения identity предоставляет `fixture.IDENTITY`; изменённые данные означают
другую задачу и не проходят этот механический контракт.

```powershell
.venv-training/Scripts/python.exe -m labs.01_pytorch_foundations.exercises.resume_training.evidence generated-reports/training-resume
```

Validator проверяет bytes/identity, повторяет непрерывное обучение, сравнивает traces
с реальными вычислениями, загружает итоговые веса и выполняет validation inference
по snapshot. Затем сверяет checkpoint с шагом 3 и реально повторяет resume через
вашу функцию в свежем процессе; временные результаты хранятся отдельно.
Совпадение двух придуманных traces недостаточно. Допуски float32: rtol=1e-5,
atol=1e-6; ID, шаги, курсор точны; следующий draw каждого RNG совпадает точно.

Unit: негативные состояния, cursor и отсутствие алиасов. Integration: 7 против
3+4 в новом процессе и граница эпохи 4+3. Smoke: отдельный скалярный checkpoint I/O,
не готовая реализация capture/restore. Evaluation: фактические traces и replay;
это не оценка качества на реальных данных. Review: объяснение и защита остаются
`REQUIRES_REVIEW` даже после всех автоматических проверок.

Подсказки: сначала перечислите всё изменяемое состояние; затем объясните, куда
показывает cursor после короткого батча; отдельно проверьте momentum buffers;
наконец проверьте каждую RNG на следующем draw. Почему одинакового seed после
перезапуска недостаточно? Почему model.state_dict без копии может измениться?
