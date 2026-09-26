# Plan a library index refresh

Difficulty: Medium

## Prerequisites and time

Python dictionaries and sets, immutable records, and the Module 06 ingestion lesson. Estimated time: 45–60 minutes.

## Goal and TODO boundary

Implement `plan_index_sync` to compare a current source catalog and an index
snapshot. Validation and result records are provided. Return a plan only; this
exercise does not write an index or delete files.

## Contract

- Both inputs are tuples of `Revision(document_id, revision)`.
  Both fields are nonblank strings, preserved exactly. IDs are unique within each
  snapshot. Invalid records or duplicate IDs raise `ValueError`, even if duplicate
  revisions agree.
- Revision tokens are opaque: compare exact equality only. Do not parse a number,
  infer age, compare lexically, or assume a lower-looking revision is stale.
- Source-only IDs become `create`; IDs on both sides with unequal revisions
  become `update`. These groups hold the **source** Revision records.
- Indexed-only IDs become `delete`; shared IDs with equal revisions become
  `unchanged`. These groups contain ID strings.
- Return `SyncPlan(create, update, delete, unchanged)`, with each group sorted by
  ascending exact document ID. Every ID belongs to exactly one group.
- Empty source deletes all indexed IDs; empty index creates all source records;
  both empty produce four empty tuples. Do not mutate or retain the snapshots.

## Hand-calculated example

Source: `a:v1, c:v2, z:new`; index: `old:v1, c:v1, a:v1`.
Create z:new, update c:v2, delete old, and leave a unchanged.
Source a:v1 compared with indexed a:v9 still schedules an update to source v1.

## Optional hints

Think in terms of the union of document IDs. A revision comparison is useful only
after you know which side contains the document.

## Run and completion

From the repository root:

```powershell
uv run pytest modules/06_rag/exercises/index_sync -q -rx
```

Implement only the named function in `starter.py`; keep the tests intact. The
untouched algorithm raises `NotImplementedError` and appears as expected-incomplete
(`xfail`) through `roadmap_tools.exercise_call`. Supplied validation checks pass
already. Completion requires every test to pass with **zero xfails**.
