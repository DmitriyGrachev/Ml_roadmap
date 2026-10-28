# Detect duplicate transactions

## Goal

Return the transaction IDs that occur more than once in an iterable of transaction rows.

## Difficulty

Beginner

## Estimated time

20–30 minutes

## Edit

Edit only `modules/01_python_core/02_collections/exercises/detect_duplicates/starter.py`.

## Requirements

- Accept any iterable of mappings, including a one-shot generator.
- Require every row to contain an `id` whose value is a nonblank string; otherwise raise `ValueError`.
- Return each repeated ID once as a `set[str]`.
- Return an empty set for empty input or when all IDs are unique.

Здесь iterable — источник элементов для обхода. В отличие от списка, одноразовый
генератор (one-shot generator) выдаёт элементы постепенно и не начинает обход
заново после исчерпания. Писать собственный генератор в этом задании не требуется;
подробный механизм будет в [уроке 07](../../../07_iterators_generators/README.md).
Эта ссылка — будущее пояснение, не новый prerequisite текущего упражнения.

## Acceptance criteria

Repeated IDs are detected without consuming the input twice, validation remains active, and the tests pass.

## Run

`uv run pytest modules/01_python_core/02_collections/exercises/detect_duplicates -q -rx`

## Hints (optional)

Consider set membership and a second set for values already known to repeat.
