# Curriculum extension implementation plan

> Execution: bounded parallel module work, shared integration in the main task, then review and verification.

**Goal:** Implement Modules 04–05 and provide neutral Medium practice in all Modules 01–08.

**Architecture:** Preserve the existing lesson/example/starter/test structure and catalog-driven CLI.
Student solutions remain absent. Modules 06–08 gain standalone practice, not complete courses.

**Tech stack:** Python 3.12, uv, pytest, Ruff, strict mypy, NumPy/Pandas, scikit-learn,
FastAPI/Pydantic; no paid API dependencies.

**Scope source:** The user's request to add two modules, clarified to include neutral Medium tasks
in every module 01–08. Continue in the explicitly named project directory; preserve existing work.

## Independent deliverables

- [x] Module 04: six lessons, executable synthetic examples, four Medium exercises covering
  group splits, mixed-feature pipelines, model comparison and evaluation reports.
- [x] Module 05: six lessons, offline examples, five Medium exercises covering messages,
  event validation, context budgets, answer evaluation and bounded retries.
- [x] Neutral practice: one standalone Medium task in each of Modules 01, 02, 03, 06, 07 and 08.
- [x] Integration: catalog entries, lesson progress, root roadmap, neutral practice index,
  scikit-learn environment/lock and expanded type-check coverage.
- [x] Verification: focused behavior tests, all examples, catalog/CLI/link checks, complete pytest,
  Ruff lint/format, mypy and locked dependency checks. Review the new material for learner-facing defects.

## Contracts and review focus

- New TODO boundaries must remain genuinely incomplete and use the established `exercise_call` helper.
- Tests must reject wrong outputs, boundary handling, leakage and invalid input; an `XFAIL` is not a solution.
- Fit preprocessing only on training data; choose model settings without consulting final test labels.
- Treat prompt data as untrusted. Structured output validity does not establish factual accuracy.
- Use offline doubles to test LLM application behavior, not to claim model capability.
- Future-module READMEs must distinguish available practice from deferred full courses.
- Shared files belong to the main integration task; module contributors have disjoint write scopes.
- Preserve existing progress markers and avoid unrelated cleanup, commits, publishing or external actions.

## Completion evidence

- Complete suite: 544 passed, 5 skipped, 521 expected-incomplete, no failures.
  Optional PostgreSQL and Windows symlink checks account for skips; one upstream Starlette/AnyIO
  deprecation warning remains unchanged.
- Ruff lint and format checks passed; strict mypy passed for 347 source files.
- Dependency lock validated (136 packages); environment validation and focused CLI commands passed.
- All 125 tracked/new Markdown files checked for local links; no broken links or artifact violations.
- Independent review of Modules 04–05 and integration resolved one categorical-dtype ambiguity
  with an explicit object-dtype input schema and an all-missing categorical regression test.
- ML and LLM authors verified exercise contracts with temporary in-memory implementations;
  no answers were saved. All distributed student boundaries remain incomplete.
