# Code review — Isolate an API test fixture

## Goal

Refactor a deliberately coupled FastAPI characterization fixture so every test owns its application,
service state, dependency overrides, and client lifecycle without changing observable API behavior.

## Difficulty

Intermediate.

## Estimated time

35–50 minutes.

## Allowed edit files

Edit only:

- `modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/review_me.py`
- `modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/test_characterization.py`

Do not change the request data, expected status codes, or expected response bodies to make the suite
pass.

## Starting point

The fixture works, but a module-scoped application and service share mutable payment state. Its client
fixture installs a dependency override, returns an unclosed client, and never clears the override.
Distinct business identifiers keep the current characterization cases deterministic; they do not make
the fixture isolated.

## Requirements

- Create a fresh application and service for each test invocation.
- Replace the returning client fixture with a yield-based fixture that closes the client and clears
  dependency overrides even when a test fails.
- Keep dependency injection visible; do not bypass the API by calling the service from the tests.
- Preserve both parameterized invocation orders and every complete JSON assertion.
- Keep the suite independent of Docker, PostgreSQL, network calls, sleep calls, and timing thresholds.

## Preserved behavior

- `POST /review-payments` returns `201` and the complete accepted-payment payload.
- `GET /review-payments/{payment_id}` returns `200` and that same complete payload.
- Decimal-looking amount strings, currencies, business identifiers, and response field names remain
  unchanged.

## Acceptance criteria

- Both `create-read-create` and `create-create-read-reverse` cases pass in every run.
- No application, service dictionary, dependency override, or `TestClient` lifecycle leaks between
  test invocations.
- The characterization assertions continue to test the HTTP boundary rather than a fake or mock.
- The command succeeds three consecutive times from the repository root without `pytest-repeat`.

## Commands

Run the suite once from the repository root:

```powershell
uv run pytest modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/test_characterization.py -q
```

Then repeat the same root-relative command in fresh pytest runs:

```powershell
1..3 | ForEach-Object {
    uv run pytest modules/02_python_backend/08_api_integration_testing/exercises/api_test_review/test_characterization.py -q
}
```

## Optional hints

- An application factory makes ownership clearer than resetting a global dictionary.
- A fixture can `yield` from inside a `with TestClient(...)` block and clean overrides in `finally`.
- Cleanup belongs to the fixture that installed the override.

## Review checklist

- [ ] Is every mutable object created inside the test or its fixture?
- [ ] Does cleanup run when an assertion or request fails?
- [ ] Are dependency overrides empty after fixture teardown?
- [ ] Is the client closed by the fixture that opened it?
- [ ] Do both parameterized invocation orders retain their original status codes and full JSON bodies?
