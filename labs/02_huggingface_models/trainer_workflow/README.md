# Trainer и Datasets: проверяемый цикл обучения

ID: `lab-hf-trainer-workflow`. Optional group: `trainer`. Материалы готовы;
learner boundaries остаются TODO. Случайный author smoke не даёт learner credit.

## Перед началом

Пройдите [основную lab02](../README.md), её [теорию](../theory.md), validation,
оценку и PyTorch loop. Здесь нужно уже понимать batch, logits, cross-entropy,
optimizer step, split и разницу `eval()`/`inference_mode()`.

```bash
uv sync --group trainer
uv run --group trainer python -m labs.02_huggingface_models.trainer_workflow.example
uv run --group trainer python scripts/learn.py test lab-hf-trainer-workflow
```

Пример — **RANDOM_LOCAL_MECHANICS_ONLY**: локальный словарь из восьми токенов,
случайный BERT (1 блок, hidden=16, 2 головы), CPU, один поток. Первый Trainer
выполняет 2 optimizer steps, второй возобновляет checkpoint до шага 3; суммарно
не больше 4 обновлений даже при выборе самого раннего checkpoint. Это проверка
механизма, не pretrained модель и не оценка качества. Каталог результата должен
быть новым; default `artifacts/trainer-author-smoke/` игнорируется git. Удаляйте
только собственный результат перед повторным запуском либо передайте другой
`--output`. Import ничего не обучает и не загружает. Обычный pytest запускает
только этот ограниченный локальный smoke, без сети и без весов с Hub.

## Учебный контракт

Реализуйте [starter.py](starter.py). Авторский example не является реализацией
этих функций и не должен вызываться из learner orchestration.

| Boundary | Точный контракт |
| --- | --- |
| `tokenize_dataset(dataset, tokenizer, max_length)` | Реальный `Dataset.map(..., batched=True)`, `truncation=True`, без padding; удалите **все** исходные столбцы через `remove_columns=dataset.column_names`, верните inputs и `labels`. |
| `build_collator(tokenizer)` | `DataCollatorWithPadding`, padding до максимальной длины **текущего** batch, CPU long tensors. |
| `make_training_arguments(output, config)` | `TrainingArguments`: CPU, eval/save каждое обновление, `load_best_model_at_end=True`, accuracy, `greater_is_better=True`, `report_to='none'`, не удалять optimizer/scheduler/RNG state. |
| `compute_metrics(evaluation)` | Аргмакс logits `[N,C]`, accuracy по `[N]` labels; malformed, пустые/nonfinite данные отвергнуть. |
| `train_model(model, tokenizer, splits, output, config, resume_from_checkpoint=None)` | Проверка split IDs и обеих label mappings, вызов предыдущих четырёх boundaries, actual Trainer, validation selection, test после выбора, safe save/local reload. |

`RunConfig(max_steps=2, batch_size=2, max_length=32, learning_rate=0.0005, seed=17)`
— frozen dataclass. `1 <= max_steps <= 100`, batch_size>0, max_length>=2,
seed>=0 — целые без bool, learning_rate конечный положительный. Это явно
заданный бюджет ручного learner эксперимента, а не гарантия качества. Author smoke
сохраняет прежний предел <=4 обновлений; тесты не запускают 100 шагов.
Установите `save_total_limit=2`: не больше двух Trainer checkpoints плюс selected
export `final/`; проверяйте диск до увеличения бюджета.

Каждый split — list `{id: str, text: str, label: int}`. Ровно `train`,
`validation`, `test`; все непустые. ID уникальны и между splits. Сначала найдите
дубликаты/семейства перефразировок и разделите по семье, затем присвойте ID.
Одна лишь уникальность ID не доказывает независимость текстов. `id2label` —
непрерывные IDs с 0, `label2id` — обратное отображение. Не переименовывайте
логиты после обучения, чтобы «подогнать» метрики.

Возвращаемый dict: `history` (сырые eval-строки Trainer.state.log_history),
`best_metric`, `best_checkpoint`, `global_step`, `predictions`, `references`,
`split_ids`, `model_identity`, `reload_identity`, `tokenizer_identity`, `checkpoint_path`.
`checkpoint_path` — safe final модель и tokenizer; identities — SHA-256 от
имён и CPU bytes параметров в фиксированном порядке. В `history` сохраните
`step`, `eval_loss`, `eval_accuracy`; `best_metric` равен максимуму accuracy,
а выбранный checkpoint должен существовать. При равенстве оставляйте правило
Trainer, не выбирайте по test. Reload через Auto loaders с
`local_files_only=True`, `trust_remote_code=False`, `use_safetensors=True`.
Для resume требуется полный `checkpoint-N`, не только финальные веса.

## Из строк в batch

Например, tokenizer локального smoke добавляет `[CLS]` и `[SEP]`:

| Текст | После map | После collator в одном batch | Attention mask |
| --- | --- | --- | --- |
| red | `[2,5,3]` | `[2,5,3,0]` | `[1,1,1,0]` |
| blue square | `[2,6,7,3]` | `[2,6,7,3]` | `[1,1,1,1]` |

`map` меняет представление строк; collator создаёт batch непосредственно перед
forward. Padding внутри map до глобального max_length тратит вычисления и скрывает
эту границу. `id`, `text`, audit metadata не должны попадать в forward. Label
сохраняется отдельно: map возвращает `labels`, а не удаляет целевую переменную
вместе с исходными колонками. Нельзя оставлять текст с подсказкой к ответу.

`compute_metrics` получает numpy logits без softmax: argmax от logits и softmax
совпадает. Среднее вероятностей по всему batch не является accuracy. Для logits
`[[1,8],[3,-1],[2,0]]` predictions=`[1,0,0]`; references=`[1,0,1]`, accuracy=2/3.
Для несбалансированных живых данных дополнительно запишите confusion matrix и
macro-F1 в анализе; smoke accuracy не переносится на другую предметную область.

## Кривые и checkpoint

Trainer считает optimizer steps, а не число токенов и не число эпох. С
accumulation=1, batch=2 и четырьмя train строками два шага — один проход;
последний неполный batch тоже учитывается. Для больших данных это уже иная доля
эпохи. Сопоставляйте train loss и validation loss по **одному шагу**, не по
порядковому номеру записи в log_history: там есть и training, и evaluation rows.

Если train loss снижается, а validation loss растёт, возможен overfit; при
маленькой validation выборке accuracy меняется ступенями и может оставаться
неподвижной. Это не оправдание дорисовать кривую. Сохраняйте сырые строки и
объясняйте число примеров, class balance и неопределённость. Не обещайте
монотонного улучшения на 2–4 случайных обновлениях. Best checkpoint определяется
**заранее выбранной** validation метрикой. Минимальная validation loss и максимум
accuracy могут быть на разных шагах; в этой лабораторной выбирается accuracy.

Resume восстанавливает weights, optimizer, scheduler, RNG и global_step.
Загрузка только `final/` — новый запуск с весами, а не продолжение той же траектории.
При изменении max_steps расписание LR может отличаться от непрерывного запуска;
в отчёте укажите отличие и не утверждайте идентичность траекторий.

## Ваш локальный pretrained эксперимент

Загрузка ресурсов — отдельное явное действие. Для уже доступного snapshot из
lab02 используйте её [download](../download.py). Для собственного источника
сначала изучите model/dataset cards, зафиксируйте revision, лицензию и список
файлов; сетевую загрузку выполните отдельно, например:

```bash
hf download YOUR_MODEL --revision EXACT_REVISION --local-dir .model-cache/trainer-source
```

Эта команда — шаблон, не выполнялась автором. Snapshot должен иметь подходящую
classification голову и **точные** label mappings, либо подготовьте локальную
голову отдельно с явным seed и зафиксируйте эту операцию. Не выбирайте
`ignore_mismatched_sizes=True` без объяснения и не называйте новую голову pretrained.

Подготовьте JSON `{dataset_source, model_source, id2label, splits}`; source
включает repo/revision/license и преобразования. `splits` имеют схему выше.
Напишите отдельный review Markdown: семейства похожих текстов, две неоднозначные
метки, минимум одна ошибка модели, новый домен и ограничения малого бюджета.

```bash
uv run --group trainer python -m labs.02_huggingface_models.trainer_workflow.run \
  --snapshot .model-cache/trainer-source --dataset data/my-trainer.json \
  --review data/my-trainer-review.md --output artifacts/trainer-learner
uv run --group trainer python scripts/learn.py check lab-hf-trainer-workflow
```

Runner работает только с явным локальным snapshot, записывает source claims,
SHA-256 входного JSON и safetensors, predictions/references/split IDs, history и
reload identity. Ошибка learner TODO не создаёт успешный report. Default strict
artifact — `artifacts/trainer-learner/report.json`. Другой output перед strict
проверкой нужно явно перенести на этот путь. Запуск smokes, skips, xfails,
скопированный авторский JSON и заполненное поле human_review не доказывают
авторство; преподаватель проверяет новый домен и реальную разметку вручную.

Перенос освоен, когда вы можете объяснить каждую колонку map, воспроизвести batch
с маской, связать eval step с сохранённым checkpoint, возобновить optimizer state,
сравнить logits до/после reload и назвать ограничения test, не подбирая по нему LR.

### Проверка сохранённого live артефакта

Strict gate заново загружает `checkpoint_path` через локальные safe Auto loaders,
считает fingerprint реальных параметров и сравнивает с `model_identity`. Сохранённый
fast tokenizer обязателен (`tokenizer.json`, `tokenizer_config.json`);
`tokenizer_identity` фиксирует vocabulary, normalizer, special tokens и стороны
padding/truncation. Тест выполняет короткий inference сохранённой пары. Равные
строки identity в JSON без файлов не проходят. Runner проверяет эти условия до
записи report. Удаление или изменение checkpoint/tokenizer делает report неполным.
