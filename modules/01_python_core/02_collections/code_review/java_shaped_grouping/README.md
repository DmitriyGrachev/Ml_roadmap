# Review Java-shaped transaction grouping

## Difficulty

Intermediate

## Estimated time

30–45 minutes

## Observed smell

`group_transactions` is correct, but it uses index-controlled loops, parallel temporary
collections, and a boolean search flag. The structure obscures the grouping rule and creates more
moving parts than the behavior requires.

## Reproduce

Run exactly:

`uv run pytest modules/01_python_core/02_collections/code_review/java_shaped_grouping -q`

The characterization suite passes before refactoring and must remain green throughout the review.

## Allowed edit

Edit only
`modules/01_python_core/02_collections/code_review/java_shaped_grouping/review_me.py`.

## Behavior that must remain

- Group by `user_id` and expose groups in first-seen user order.
- Keep transactions in their original order inside each group.
- Retain every field and exact `Decimal` value from each row.
- Accept empty input and return an empty mapping.
- Do not mutate the input collection or any transaction row inside it.

## Hints (optional)

Look for collection operations that express “get or create this group” directly. Prefer iteration
over elements to manually tracking indices, and give intermediate names only when they clarify the
business rule.

## Acceptance criteria

The characterization suite remains green after the index loops, redundant temporary collections,
and boolean search flag are removed. The public function and typed row shape remain available.

## Self-review checklist

- [ ] Can a reader identify the grouping rule without tracing indices?
- [ ] Is first-seen ordering preserved deliberately?
- [ ] Are full rows and exact `Decimal` values retained?
- [ ] Did I keep the input unchanged and the characterization tests green?
