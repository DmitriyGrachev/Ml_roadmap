# Debug leaking audit tags

## Difficulty

Beginner

## Estimated time

15–25 minutes

## Observed symptom

Calling `append_audit_tag` without an explicit tag list can expose tags added by an earlier call.
Independent audit operations therefore influence one another.

## Reproduce

Run exactly:

`uv run pytest modules/01_python_core/03_functions/debugging/mutable_defaults -q --runxfail`

The starter is intentionally broken, so this command must fail before your change and pass after it.

## Allowed edit

Edit only `modules/01_python_core/03_functions/debugging/mutable_defaults/broken.py`.

## Behavior that must remain

- `append_audit_tag` accepts a tag and an optional caller-provided list.
- It appends the tag and returns the list containing it.
- When the caller supplies a list, that same list remains the target of the append.
- Calls that omit the list remain independent from earlier calls.

## Hints (optional)

Review when Python evaluates default argument expressions and distinguish “argument omitted” from
“caller supplied this list.” Keep the public function name and return type unchanged.

## Acceptance criteria

The reproduction command passes, two default-list calls have isolated results, and explicit-list
behavior is preserved without module-level mutable state.

## Self-review checklist

- [ ] Did I reproduce the failure before editing the allowed file?
- [ ] Does each omitted-list call begin with independent state?
- [ ] Does an explicitly supplied list still receive the new tag?
- [ ] Did I avoid changing or weakening the test?
