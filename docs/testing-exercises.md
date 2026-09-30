# Testing exercises

## Three learner states

Exercise tests distinguish three outcomes:

1. **Expected-incomplete:** an untouched starter boundary raises `NotImplementedError` and the helper marks that one boundary as expected-incomplete.
2. **Failed attempt:** an incorrect result, import error, syntax error, assertion failure, or unexpected exception fails normally.
3. **Passed solution:** a correct implementation passes the exercise test.

This keeps the repository health check useful without pretending the learner's work is already complete.

## Run the narrowest useful command

Start from the repository root. Each exercise README names its focused test command;
`uv run python scripts/learn.py test python-collections` delegates only to catalog-owned test
targets. Use `uv run pytest` to check overall repository health.

The full suite also contains maintainer checks that require the distributed starter template to
remain unsolved (`tests/integration/test_repository_hygiene.py`). Once you implement a starter,
those particular assertions can fail by design. Judge your answer using the focused task command,
not by restoring `NotImplementedError` to satisfy template hygiene.

For neutral practice in every module, see the [Medium exercise map](neutral-practice.md).
Modules 04–08 examples run locally; provider doubles test LLM application contracts, not the
quality or safety of a real model. Retrieval fixtures and operational simulations likewise do not
establish live retrieval quality or production readiness. An untouched starter remains `XFAIL`,
not a passed solution.

## Строгий зачёт выбранного материала

`uv run python scripts/learn.py check python-word-index` запускает только targets
этого ID. `test` сохраняет прежний health-смысл; `check` отклоняет required
skip/xfail, NotImplementedError, failures и отсутствие обязательных tests/results.
TODO соседних уроков не влияют на выбранный зачёт. Учебный progress всегда ручной.

Для labs: `uv run --group training python scripts/learn.py check lab-pytorch`
или `lab-huggingface`. Без training dependencies получите понятную ошибку установки,
а не ложный PASS. Optional GPU/live помечены NOT_RUN и не блокируют CPU-зачёт.
Это не LIVE_VERIFIED и не доказательство model quality.
Каждый старый lab ID запускает только свои исходные `test_example.py`,
`test_starter.py` и `test_report.py` (PyTorch) либо `test_protocol.py`
(Hugging Face). Новые соседние упражнения имеют собственные ID и не расширяют
зачёт старой лабораторной. `test ID` остаётся health-проверкой с допустимым xfail;
`check ID` требует завершённых обязательных тестов и отклоняет required skip/xfail.

Unit tests проверяют контракты. Integration smoke проверяет wiring и reload.
ML evaluation измеряет обобщение на конкретных данных; успешный pytest его не заменяет.
Отчёт должен содержать ваши реальные значения/файлы и самостоятельный анализ;
структурный валидатор не оценивает научную добросовестность или глубину выводов.
Старый PyTorch schema-1 report проверяет traceability и арифметику заявленных
predictions, но не воспроизводит inference из checkpoint. Новые experiment checks
должны пересчитать inference/trace из сохранённых bytes и сопоставить row IDs.
Любое текстовое объяснение остаётся `REQUIRES_REVIEW` до проверки человеком.

## When a test fails

Read the assertion and the stated acceptance criteria before changing code. Do not modify test expectations to accept an implementation that violates the exercise contract. Preserve a passing regression test whenever you repair a genuine defect.

## Quality checks

Run `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy` before treating a learning change as complete. See the [learning rules](learning-rules.md) for the associated working habits.
