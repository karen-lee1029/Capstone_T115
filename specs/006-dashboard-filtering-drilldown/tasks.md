# Tasks: Feature-006 (US-29)

Implementation starts only after the independent SDD review. Work in `student_attrition_risk_app/`.
[P] = can run in parallel.

## Phase 1 — Setup

- [ ] T001 Confirm baseline: `uv run pytest` 24 failed / 285 passed / 14 skipped; ruff 1 finding
- [ ] T002 Obtain the global-filter page and table default-sort shapes from a workspace export (R-3); record in research.md

## Phase 2 — Repair base failures (US5; Q3, Q15)

- [ ] T003 [P] Repair `tests/test_dashboard.py` per plan D-8 / contract C-6
- [ ] T004 [P] Repair `tests/test_ui.py` per plan D-9
- [ ] T005 Full suite: 0 failures before any dashboard change

## Phase 3 — US-29 tests first (`tests/test_dashboard_filtering.py`)

- [ ] T006 Helpers: load repo JSON; load base JSON via `git show 0409d7e:...` (skip if unavailable)
- [ ] T007 [P] US1 checks FR-001 – FR-007
- [ ] T008 [P] US2 check FR-008
- [ ] T009 [P] US3 checks FR-010 – FR-013
- [ ] T010 [P] US4 and preservation checks FR-014 – FR-017
- [ ] T011 Run new file — expect red

## Phase 4 — Dashboard

- [ ] T012 US1: add `global_filters` page with 8 filters (C-1, C-4); remove `310fbbb0`; widen `c2d55445`
- [ ] T013 US2: confirm graph queries on every page (no change expected)
- [ ] T014 US3: add three drill tables (C-2, C-4)
- [ ] T015 US4: add `how_to_filter` (C-3); move note/footer widgets (C-4)

## Phase 5 — Verify and record

- [ ] T016 New file green; full `pytest` 0 failures; ruff only the base finding
- [ ] T017 Fill `teammate-changes.md` commits/lines; confirm traceability test names
- [ ] T018 Implementation handoff for Codex Code Reviewer
