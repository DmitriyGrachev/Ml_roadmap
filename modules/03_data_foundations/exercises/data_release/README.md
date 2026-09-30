# Неудобные данные: контроль выпуска

`data-release-study` · материалы READY · самостоятельный контроль №1.
Реализация ученика TODO; его эксперимент NOT_RUN; защита REQUIRES_REVIEW.

Цель — выпустить воспроизводимые данные из несовместимых локальных источников,
обосновать качество и использование памяти. Формат внутренних этапов выбираете вы.
Изменяйте `starter.py`, при необходимости добавляйте свои внутренние модули.
Не меняйте fixtures, инфраструктуру, tests и соседние TODO ради зачёта.

## Prerequisites

- `python-io`: [файлы](../../../01_python_core/06_exceptions_io/README.md).
- `python-paged-stream`: [iter_pages](../../../01_python_core/exercises/paged_stream/README.md).
- `python-testing`: [тестирование](../../../01_python_core/09_testing/README.md).
- `data-quality-report`: [независимые дефекты](../../03_data_quality/exercises/quality_report/README.md).
- `data-library-joins`: [ключи и cardinality](../library_joins/README.md).

Сначала завершите эти границы. Переиспользуйте `iter_pages` там, где требуется
постраничное потребление, и уже изученные контракты качества/связей; не создавайте
вторую реализацию prerequisite внутри упражнения. Числовые имена пакетов допускают
`importlib.import_module`. Конкретная внутренняя архитектура здесь не предписана.

## Данные и внешняя семантика

`build_release(inputs: Sequence[Path], output_dir: Path, *, batch_size: int) -> Path`
получает четыре файла из одного каталога: `source_a.csv`, `source_b.jsonl`,
`labels.csv`, `provenance.json`. Возвращает `output_dir / "manifest.json"`.
Каталог результата должен быть новым, иначе `FileExistsError`, без append/перезаписи.
Неположительный `batch_size` — `ValueError` с `batch_size` в сообщении до создания результата.

Входы конечные, UTF-8, одна запись на физическую строку, без многострочных CSV-полей.
CSV содержит `id,amount`, JSONL — `business_id,value`. ID — непустая строка после
strip; amount — конечное положительное число, bool недопустим. В labels CSV колонки
`id,label`, метки `yes`/`no`; повтор той же метки допустим, разные метки неоднозначны.
Некорректный формат строки сохраняется как отклонённая запись. Нет внешних загрузок.
Fixture содержит 8 строк данных, несколько схем, повтор ID, NaN, пустой ID,
неоднозначные labels и испорченный JSON. `provenance.json` задаёт origin, license,
SHA-256 точных байтов каждого источника, включая labels; проверяйте их до выпуска.

Каждая исходная строка ровно один раз представлена в одном JSONL:

| Выход | Правило rubric v1 (приоритет сверху вниз) | reason |
| --- | --- | --- |
| `rejected.jsonl` | отсутствует корректный ID или amount | `invalid` |
| `review.jsonl` | ID встречается более одного раза во всех строках источников | `duplicate` |
| `review.jsonl` | для оставшегося ID нет ровно одной различной метки | `label` |
| `accepted.jsonl` | остальные строки | `accepted` |

Не выбирайте произвольную строку повторного business ID. Даже совпадающие дубликаты
идут на review: это сохраняет cardinality и делает решение проверяемым.
Каждая выходная строка имеет поля `source` (имя файла), `line` (физическая строка,
CSV data начинается с 2), `row_id`, `business_id`, `amount`, `label`, `reason`, `split`.
`row_id` — lowercase SHA-256 UTF-8 строки `source:line`.
`business_id`/`amount` — нормализованные значения или JSON null при соответствующем
дефекте; при непарсящейся строке оба null. Метка равна единственной различной метке
этого ID либо null, в том числе у rejected/review. Порядок строк детерминирован.
Для accepted: SHA-256 UTF-8 business ID, целое hex modulo 10: 0–1 → `test`,
2–9 → `train`; у остальных `split=null`. Это фиксированный учебный split,
не утверждение о пригодности для временных или причинных ML-задач.

`splits.json` — объект row_id → split, только accepted.
`schema.json` — `{"version": 1, "rubric_version": 1}`: версии этой документированной
схемы и rubric. Изменение правил требует новой версии, а не тихой замены labels.
Все три JSONL присутствуют, даже пустые. Итоговые counts для fixture: 2/3/3.

## Manifest и ресурсы

Завершённый manifest — JSON объект со следующими обязательными полями:

- `schema_version=1`, `exercise_id="data-release-study"`, `rubric_version=1`,
  `complete=true`; выставляйте завершение только для полностью готового выпуска.
- `sources`, `origin`, `license` — согласованы с входным provenance и реальными байтами.
- `dataset_sha256` — SHA-256 от UTF-8 `json.dumps(sources, sort_keys=True)`;
  `split_sha256` — SHA-256 байтов `splits.json`.
- `config` содержит `batch_size`; `counts` содержит `accepted`, `rejected`, `review`.
- `artifacts`: имя → lowercase SHA-256 для всех трёх JSONL, `splits.json`,
  `schema.json`, `memory.md`. Не включайте абсолютные пути, timestamps или сам manifest.
- `resources`: целые `buffer_limit_pages` (c от 1 до 8), `peak_buffer_records`
  (0…c×B), `index_limit` (>0), непустая строка `index_strategy`.
  В `memory.md` укажите единицы index_limit, фактически наблюдавшийся максимум,
  ограничения ключей/индекса и поведение при исчерпании ресурса.

Бюджет записей рабочих буферов — c×B при фиксированном B. Отдельно обоснуйте
state глобальных ID/labels: он должен иметь конечный предел или храниться на диске
с ограниченным кэшем. Все строки в list не становятся streaming от названия.
Для ручного опыта выберите два конечных размера N при одном B, укажите точные
команды, размер записи, метрики и границы измерений. Python allocations (например,
tracemalloc) не равны RSS процесса: native allocations, allocator и ОС различаются.
Никакого зачёта по порогу RSS или секундомеру нет.

Тест оборачивает доступную границу `iter_pages` и наблюдает consumed records и
размер выданной страницы B. Если ваша архитектура не проходит через эту точку,
тест явно пишет `not_observed`; добавьте свой наблюдаемый boundary в ручную защиту.
Он не подменяет prerequisite и сначала вызывает именно `build_release`.
Declared buffers проверяются на согласованность c×B, но это заявление автора,
не доказательство отсутствия скрытого удержания записей. Даже наличие page trace
не доказывает общую память. Маленький read-only validator сам может индексировать
весь fixture; его потребление памяти не характеризует learner pipeline.

## Команды и критерий

Из корня репозитория; в PyCharm используйте тот же интерпретатор проекта:

```powershell
uv run python scripts/learn.py test data-release-study
uv run python scripts/learn.py check data-release-study
uv run python -m modules.03_data_foundations.exercises.data_release.generate <NEW_INPUT_DIR> --records 200 --seed 23
uv run python -m modules.03_data_foundations.exercises.data_release.evidence <EXISTING_RELEASE_DIR> --input-dir <INPUT_DIR>
```

Генерация — только явная команда с новым путём; default 200, никогда 3 GB.
Imports, pytest и sync не запускают генерацию пользовательского набора. Тесты
генератора используют только собственные временные каталоги. Выпуск запускаете
своим вызовом `build_release`, затем повторяете в **другой новый** каталог: байты и
hash должны совпасть, входы должны сохраниться. Проверка evidence ничего не создаёт.

Unit проверяет генератор и отрицательные случаи evidence; smoke — маленький
настоящий learner release, повтор и сохранность существующих файлов. Здесь нет
обучения модели и ML evaluation. `test` допускает xfail только от TODO;
`check` требует выполненных student assertions без xfail/skip. Объяснение решений,
лицензии, качество данных, независимость split и memory report остаются
`REQUIRES_REVIEW` до проверки человеком; hashes подтверждают согласованность,
а не юридическую подлинность заявления origin/license.

## Подсказки по этапам

1. Сначала сформулируйте инварианты сохранения строк и поведения при конфликте.
2. Проверьте, что разные схемы не меняют смысл ID, labels и чисел.
3. Для каждого ресурса назовите владельца, предел и свидетельство измерения.
4. Объясните, почему оборванный выпуск не может выглядеть завершённым.
