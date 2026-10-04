# Tasks: Feature-006 (US-29)

Q16 – Q19 answered 2026-10-04 (spec Clarifications). Work in `student_attrition_risk_app/`.
[P] = can run in parallel.

## Phase 1 — Setup

- [x] T001 Confirm baseline: `uv run pytest` 24 failed / 285 passed / 14 skipped; ruff 1 finding
- [x] T002 Obtain the global-filter page and table default-sort shapes from a workspace export (R-3); record in research.md

## Phase 2 — Repair base failures (US5; Q3, Q15)

- [x] T003 [P] Repair `tests/test_dashboard.py` per plan D-8 / contract C-6 (live one-page check left unchanged, Q18 = a)
- [x] T004 [P] Repair `tests/test_ui.py` per plan D-9
- [x] T005 Full suite before the dashboard change: 1 expected failure (Q20 label count 5, needs the new tables); all 24 base failures fixed

## Phase 3 — US-29 tests first (`tests/test_dashboard_filtering.py`)

- [x] T006 Helpers: load repo JSON; load base JSON via `git show 0409d7e:...` (skip if unavailable)
- [x] T007 [P] US1 checks FR-001 – FR-007
- [x] T008 [P] US2 check FR-008
- [x] T009 [P] US3 checks FR-010 – FR-013
- [x] T010 [P] US4 and preservation checks FR-014 – FR-017
- [x] T011 Run new file (written alongside the dashboard edit; regression power shown by 3 mutations, see implementation handoff)

## Phase 4 — Dashboard

- [x] T011a Add the Gender Breakdown page and move Risk by Gender (D-2a)
- [x] T012 US1: add `global_filters` page with 8 filters (C-1, C-4); remove `310fbbb0`; widen `c2d55445`
- [x] T013 US2: confirm graph queries on every page (no change expected)
- [x] T014 US3: add three drill tables (C-2, C-4) with the 100,000 boundary description
- [x] T015 US4: add `how_to_filter` (C-3); move note/footer widgets (C-4)

## Phase 5 — Verify and record

- [x] T016 New file green; full `pytest` 0 failures; ruff only the base finding
- [x] T017 Fill `teammate-changes.md` commits/lines; confirm traceability test names
- [x] T018 Implementation handoff for Codex Code Reviewer, listing every quickstart matrix row as passed / failed / pending / not applicable
