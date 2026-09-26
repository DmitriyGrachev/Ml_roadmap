# Complete the remaining roadmap modules

**Request:** Continue all remaining modules after the completed 01–05 extension.
**Scope:** Full Modules 06, 07 and 08 in the established lesson/example/starter/test format.
**Audience:** Experienced Java/Spring engineer learning applied AI in Windows/PyCharm.

## Deliverables

- [x] Module 06: six RAG lessons; four new Medium exercises for authorized vector search,
  rank fusion, evidence citation checks and query-level retrieval evaluation.
- [x] Module 07: six workflow/agent lessons; four new Medium exercises for authorized tool
  dispatch, bounded agent execution, checkpoint approval/resume and trace evaluation.
  Include real local LangGraph and MCP SDK examples, with explicit protocol-version boundaries.
- [x] Module 08: six production-AI lessons; four new Medium exercises for paired release
  gates, budget ledgers, minimized event logs and canary decisions.
- [x] Preserve the three original standalone tasks byte-for-byte and link them into the course.
- [x] Integrate 18 lessons and 12 exercises into the catalog and manual progress checklist.
  Update current guides, dependency lock and course inventories without rewriting historical plans.
- [x] Verify examples, focused tests, all repository tests, Ruff, strict mypy, CLI entry points,
  local links, and preserved exercise hashes. Independently review learning contracts.

## Boundaries

Each module has one owner; shared catalog/configuration/docs/tests belong to the main integration
task. No worktrees, commits, external services, real deployments or publishing are needed.
Prior uncommitted work and learner progress belong to the user and must be preserved.

Student algorithms remain TODOs raising `NotImplementedError`; automated tests use `exercise_call`
to distinguish an untouched task from an incorrect attempt. Examples teach adjacent mechanics
without shipping the exercise answers. Temporary in-memory validation must leave no solution files.

Use short primary-source-backed explanations, five self-check questions per lesson, and clear
acceptance criteria with real edge cases. All required examples run locally and deterministically.
Synthetic embeddings, scripted models and rollout simulations must not imply measured real-world
semantic quality, universal privacy guarantees or production readiness.

## Review focus

- Authorization is enforced before retrieval ranking and before tool execution.
- Citation identity and exact evidence do not prove factual entailment.
- Approval binds the intended request/version; replay is not magically exactly-once execution.
- Evaluation keeps complete denominators, aligns identifiers and handles absent slices explicitly.
- Budget reservations and settlements cannot silently overspend or double-count retries.
- Live network tracing must not be activated by the local teaching examples.
- Historical standalone exercises remain discoverable and unchanged.

## Completion evidence — 2026-09-26

- Full repository suite: **598 passed, 5 skipped, 745 xfailed**, no failures.
  Expected-incomplete results belong to intentionally unsolved student boundaries.
  One dependency deprecation warning remains in Starlette's AnyIO portal type alias.
- Ruff check passed; format check passed for 516 Python files; strict mypy passed for
  445 source files. The dependency lock check resolved 161 packages without changes.
- All 18 new lesson examples exited successfully when run directly from the repository root.
  CLI checks passed for `rag-contracts`, `agents-langgraph-mcp`, and `production-serving`;
  environment validation and the manual progress listing also succeeded.
- Catalog inventory: 56 lessons, 64 exercises, one project. All 156 Markdown files,
  including untracked additions, passed local-link checks; repository file hygiene passed.
- SHA-256 values of all 12 files in the three original standalone exercise directories
  match their recorded pre-extension values. Existing learner progress was preserved.
- Independent curriculum reviews found no remaining material contract issues. Review-driven
  changes clarified invalid budget amounts versus insufficient capacity and added tests for
  individual agent limits, revoked/cross-workflow replay approval, and single execution on
  an unknown-outcome failure. Disposable in-memory checks accepted five conforming cases
  and rejected the corresponding faulty behaviors; no solution files were saved.
- No commits, publishing, external model calls, or deployment changes were made.
