# Versioned response cache with expiry

Difficulty: Medium

## Prerequisites and time

Python tuples, immutable dataclasses, exact key equality, and the Module 05 reliability lesson. Estimated time: 60–75 minutes.

## Goal and TODO boundary

Implement `cache_response` as a pure state transition on a supplied cache
snapshot. Validation and result types are provided. There is no clock read,
filesystem, hashing requirement, network provider, or global cache.

## Contract

- `CacheKey(prompt, model, prompt_version)` contains three nonblank strings.
  Equality is exact and case-sensitive for all components; preserve whitespace.
  The exercise assumes these are all response-affecting settings.
- `CacheEntry(key, response, expires_at)` contains any string response and a
  finite nonnegative absolute expiry. Every snapshot must have unique keys,
  including expired entries. `now` is finite and nonnegative; `ttl` is finite
  and positive, and `now + ttl` must remain finite. Numeric booleans are invalid.
- `response=None` means read; any string, including `""`, means write.
  Other response values, invalid keys, duplicate entries or invalid times raise
  `ValueError`. Validate the whole input before pruning, for reads and writes.
- First remove all entries with `expires_at <= now`. Preserve order of the
  remaining entries.
- For a read, return the matching fresh response with `hit=True`, preserving its
  expiry and position. A miss returns `response=None, hit=False` and inserts
  nothing. Reading must not extend expiry.
- For a write, remove any existing fresh entry with that key and append a new
  `CacheEntry(key, response, now + ttl)`. Return the written response with
  `hit=False`, regardless of whether a previous entry existed.
- Return `CacheResult(entries, response, hit)` with an immutable tuple snapshot.
  Do not mutate inputs or retain state.

## Hand-calculated example

An entry expiring at 12 is a hit at time 11 and a miss at time 12. Writing
`"Nine"` at time 10 with TTL 2 creates expiry 12. A key with prompt version v2
does not hit a response stored under v1, even if prompt and model match.

## Optional hints

Distinguish a missing response from an empty response. Treat expiry as an absolute
boundary and TTL as a duration; they are not interchangeable.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/05_llm_engineering/exercises/response_cache -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
