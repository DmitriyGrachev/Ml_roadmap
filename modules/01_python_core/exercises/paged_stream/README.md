# Batch a one-shot stream

Difficulty: Medium · Estimated time: 35–50 minutes

## Prerequisites

Module 01 lessons 04 (generic types), 07 (iterators/generators), and 09 (pytest).
Understand that an iterator can be exhausted and cannot necessarily be restarted.

## Requirements

Implement the generic `iter_pages(source, size)` in `starter.py`.

- Accept any iterable, including a one-shot iterator. Return an iterator yielding
  tuples with at most `size` items, preserving order and repeated values.
- `size` must be a positive integer; reject booleans and non-integers with
  `ValueError` with `size` in the message. Validation may happen on the call or first iteration, but must
  happen before pulling any source item, including for an empty source.
- Creating the iterator must not pull source items. Requesting one page may pull
  only the items in that page; do not prefetch the next page. Stopping iteration
  must leave unrequested source items available to another consumer.
- Yield the final short page. Never yield an empty page. Propagate source errors
  unchanged; do not suppress them or emit a partly filled page after an error.
- Do not mutate source collections. No networking, files, or dependencies needed.

## Example

```python
list(iter_pages(iter([1, 2, 3, 4, 5]), 2))
# [(1, 2), (3, 4), (5,)]
```

## Edge cases and optional hints

Cover empty input, exact multiples, size one, and a source that raises halfway
through a page. Consider a generator with one source iterator and a fresh page
buffer, or `itertools.islice`. Avoid converting the whole source into a list.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/01_python_core/exercises/paged_stream -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails and the pull
count test proves that consumers control how much of the source is read.
