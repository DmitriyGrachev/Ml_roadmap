# Export JSON atomically

## Goal

Write JSON through a sibling temporary path and replace the destination only after serialization
succeeds.

## Difficulty

Intermediate

## Estimated time

30–45 minutes

## Edit

Edit only `modules/01_python_core/06_exceptions_io/exercises/json_export/starter.py`.

## Requirements

- Serialize UTF-8 JSON and retain readable non-ASCII characters.
- Write to a temporary file in the destination's parent directory.
- Atomically replace the destination only after a successful write (`Path.replace` is one suitable
  interface).
- Return the destination path on success.
- On serialization or replacement failure, preserve an existing destination, remove only the
  temporary file created by this call, and re-raise the original exception unchanged.
- Do not leave a temporary path behind after success or failure.

## Acceptance criteria

Success produces the requested JSON file with no sibling debris. Both tested failure phases retain
the old destination, clean up temporary output, and expose the original error.

## Run

`uv run pytest modules/01_python_core/06_exceptions_io/exercises/json_export -q -rx`

## Hints (optional)

`tempfile` can create a unique sibling path. A `try`/`finally` block is useful when cleanup must run
for errors from more than one operation. Closing the writer before replacement keeps ownership
clear on Windows.

## Self-check

1. Why must the temporary file share the destination directory?
2. At what point may the old destination change?
3. Which path does this function own and therefore may clean up?
4. Does cleanup replace the exception raised by serialization or replacement?
5. Is the temporary writer closed before replacement runs?
