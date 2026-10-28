# Часть A: один вопрос, три классификатора

**Материалы подготовлены; pretrained experiment — NOT_RUN.** Это продолжение
[A1](../part_a1/README.md), а не повторный курс обучения моделей. Сначала выполните
[PyTorch](../../../labs/01_pytorch_foundations/README.md) и
[Hugging Face](../../../labs/02_huggingface_models/README.md), включая свой training,
validation и reload. Их student TODO и четырёхклассовый протокол здесь не меняются.

## Задача и интуиция

«Более сложная модель лучше?» — вопрос без ответа, пока модели не получили один
и тот же экзамен. Если rules проверили на простых строках, а encoder на других,
разница метрик может происходить от данных. Сравнение начинается с идентичности
документов и разбиения, а не с GPU.

```text
dataset bytes + split bytes + ordered labels
                  |
           одни test row_id
        /           |            \
     rules       TF-IDF       tokenizer → encoder → logits
        \           |            /
     predictions для тех же row_id → общие metrics
```

**Cohort** — фиксированный набор оцениваемых объектов. **Label mapping** —
соответствие номера выхода смыслу класса. `argmax=0` означает `circle` только
если сохранённое `id2label[0]` действительно равно `circle`. Нельзя взять logits
от новой модели и старый список меток только потому, что их длины совпадают.

## Разобранный локальный пример

Из корня, в уже подготовленной opt-in training среде:

```powershell
.venv-training/Scripts/python.exe -m projects.document_intelligence_lab.part_a.demo --output artifacts/document-a-teacher-001
.venv-training/Scripts/python.exe -m pytest projects/document_intelligence_lab/part_a -q
```

Выходная папка должна быть новой. Никаких загрузок из Hub нет. Пример переиспользует
готовый маленький случайный BERT из HF lab, а не создаёт второй training loop.

1. A1 создаёт 21 авторское описание фигур и обучает classical baseline только на train.
2. Берём **его** dataset/split hashes и метки `circle`, `square`, `triangle`.
3. Локальный tokenizer превращает два текста в `input_ids [2, 5]` и такую же mask.
   Это существующий tiny word-level словарь: три слова плюс два специальных токена.
4. Случайный encoder возвращает `logits [2, 3]`. Столбцы — классы, не слова.
   Максимальный logit определяет label, но не подтверждает правильность ответа.
5. Сохраняем tokenizer, config и safetensors. `encoder-manifest.json` фиксирует
   их bytes, source revision, label mapping, dataset/split, batch size и max length.
6. Повторно загружаем все три модели; пересчитываем predictions на общих шести
   test документах. Для rules/TF-IDF дополнительно проверяем совпадение с A1 artifacts.
7. `comparison.json` содержит реальные результаты этого запуска и `reload_parity`.
   Seed равен 17, training encoder не выполнялся, device — CPU. Это **teacher-random**,
   а `pretrained_quality` остаётся **NOT_RUN**, даже если случайно угаданы некоторые строки.

`protocol.py` использует существующий HF `checkpoint_predictions`: только локальные
files, safetensors, `eval`, отсутствие градиентов и remote code. Неправильный hash,
добавленный неучтённый файл или другое разбиение останавливают сравнение до inference.
Ограничение `max_length` сверяется с сохранённой конфигурацией; truncation всё равно
может убрать смысл в конце документа — проверьте это отдельно на своём материале.

Для sklearn pickle требуется явное доверие оператора к **конкретному локальному**
bundle: `compare(..., trusted_local_artifacts=True)`. Teacher включает его только
для файлов, которые сам только что создал. Не копируйте флаг для чужих загрузок:
hash проверяет целостность, а не безопасность автора pickle.

## Предварительная проверка входов — без обучения

[Preflight](preflight.py) отвечает на узкий вопрос: «Выбраны ли целые локальные
bundles и checkpoint для одного экзамена?» Он переиспользует проверки `compare`,
но не загружает pickle/веса, не делает inference и ничего не записывает.
Его можно запустить в базовой среде, где нет Torch/Transformers.

```text
3 пути + 3 заранее сохранённых pins
            ↓
проверка bytes/inventory → methods → data/split/label order
            ↓
INPUTS_VERIFIED                либо BLOCKED_INPUTS
execution: NOT_RUN             exit 2, причина в JSON
quality: NOT_EVALUATED
```

Сначала выполните teacher demo выше в новой папке. Сохранённый `comparison.json`
содержит pins именно этого запуска. Пример проверки его входов из корня:

```powershell
$partARoot = 'artifacts/document-a-teacher-001'
$partARecord = Get-Content "$partARoot/comparison.json" -Raw | ConvertFrom-Json
.venv/Scripts/python.exe -m projects.document_intelligence_lab.part_a.preflight --rules "$partARoot/a1/rules" --rules-sha256 $partARecord.bundles.rules --tfidf "$partARoot/a1/tfidf-linear" --tfidf-sha256 $partARecord.bundles.'tfidf-linear' --encoder "$partARoot/encoder" --encoder-sha256 $partARecord.encoder_manifest_sha256 --seed 17 --device cpu --max-seconds 60 --max-memory-mib 2048
```

Здесь seed/device/budgets — **запрошенные параметры будущего опыта**, не измерения.
Флаг `--device cuda` не проверяет CUDA и не переносит модель на GPU. Версия package
не доказывает работоспособность runtime. `INPUTS_VERIFIED` означает только
согласованность inventory/cohort, не обученность, корректный safetensors format,
безопасность чужих artifacts, качество, reload parity или соблюдение бюджета.
Не вычисляйте новый expected hash из изменившегося файла ради зелёной проверки:
используйте ранее защищённую operator record. Teacher record здесь принадлежит
только что созданному вашему локальному demo.

Прогноз до запуска: что произойдёт, если оставить правильные пути, но поменять
encoder pin на 64 нуля? Проверьте это отдельным вызовом, не изменяя оригиналы.
Ожидается `BLOCKED_INPUTS`, exit 2, **до** inference. Затем объясните, почему
прошедшая проверку случайная teacher модель всё ещё не считается pretrained.
Это самостоятельная вариация проверки, не решение classifier TODO.

## Типичная ошибка

Переименовать случайную модель в `pretrained`, посмотреть только accuracy и объявить
encoder победителем. Проверка save/load доказывает сохранение вычисления, не обучение.
Даже обученный encoder на короткой синтетической лексике не доказывает перенос на
реальные документы. Нужны незнакомые формулировки, группы источников и разбор ошибок.

Другой провал — посчитать метрики из старого JSON после замены tokenizer. Поэтому
сравнение заново получает predictions из сохранённых bytes, а не доверяет подписи.

## Самостоятельный перенос — REQUIRES_REVIEW

Используйте разрешённые документы из своей A1-работы; не teacher shapes и не test
для подбора параметров. Не меняйте существующий HF lab под новую задачу: отдельный
эксперимент использует её освоенные механизмы.

1. Зафиксируйте corpus, правила разметки, label order и splits. Предскажите, где
   rules, lexical features и контекст encoder будут ошибаться по-разному.
2. Сначала сохраните rules и TF-IDF bundles по [контракту A1](../part_a1/schema.md).
3. После **отдельного осознанного** получения разрешённого pretrained snapshot
   обучите/адаптируйте encoder на train, выбирайте параметры по validation. Запишите
   revision/лицензию, seed, версии, параметры обучения, max length, batch size,
   устройство, время и память. Не объявляйте загруженный backbone обученным classifier.
4. Сохраните локальный checkpoint вместе с tokenizer. Зарегистрируйте его функцией
   `register_checkpoint` с `evidence_kind="student-local"`, действительным
   `source_revision` и hashes **своего** A1 bundle. Не используйте teacher seed как
   подтверждение собственного обучения. Сохраните отдельный журнал training run.
5. Запустите `compare` с явным expected hash и доверенными собственными baseline
   artifacts. Пересчитайте результаты в новом процессе. Сравните errors по группам,
   а не только общее число. Новая teacher проверка не выдаёт зачёт этой работе.
6. По очереди измените label mapping, tokenizer и split в копии результатов:
   какой барьер должен сработать? Оригиналы не перезаписывайте.

Вопросы защиты: почему logits `[B, C]`, а не `[B, T, V]`? Что теряет truncation?
Зачем нужен сохранённый tokenizer? Может ли лучшая validation модель проиграть на
test? Что доказывает parity и чего не доказывает? Когда оставить TF-IDF в production?

Новый большой датасет, GPU и новый exercise ID для этого переноса не обязательны.
Сложность увеличивается после измеренной необходимости; на RTX 5060 начинайте с
маленького batch и одного процесса. [Ресурсные ограничения](../../../docs/compute-guide.md)
и [rubric защиты](../../../docs/project-defense.md) остаются общими.
