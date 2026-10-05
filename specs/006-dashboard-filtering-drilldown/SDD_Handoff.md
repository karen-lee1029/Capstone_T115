# SDD Handoff: Feature-006 — Interactive Dashboard Filtering and Drill-Down (US-29)

**For**: Codex SDD Reviewer · **From**: Claude Coder · **Date**: 2026-10-04
**Branch**: `agent/claude-coder-mutdg3d2`, based on `origin/main` `0409d7e` (local commit, not pushed)

## What to review

| File | Purpose |
|---|---|
| `spec.md` | Story, criterion, the product owner's 15 decisions (Q1 – Q15), 5 user stories, FR-001 – FR-027, success criteria, edge cases |
| `plan.md` | Baseline (24 failures and causes), constitution check, change map, design D-1 – D-9, test plan, risks |
| `contracts/dashboard-interaction-contract.md` | Exact filters, tables, panel text, layout, unchanged parts, repaired chart checks |
| `research.md` | Platform findings R-1 – R-7 |
| `data-model.md` | Reused fields and invariants |
| `quickstart.md` | Offline verification; product-owner publish and evidence steps |
| `traceability.md` | FR → check |
| `teammate-changes.md` | Planned edits to Karen's layout and two test files, with revert steps |
| `tasks.md`, `checklists/requirements.md` | Task order; checklist |

## Scope

- **US-29**: the dashboard definition only, plus one new test file
  (`tests/test_dashboard_filtering.py`).
- **Repair (Q3, Q15)**: update Karen's `tests/test_dashboard.py` and `tests/test_ui.py` so the 24
  base failures pass against the current design.
- **Unchanged**: no Python source, dataset, advisor page or briefing change.

## Key design decisions (all from the product owner's answers)

1. One dashboard-wide filter page with eight multi-select filters: Risk Level, Faculty, Course
   Level, Field of Education, Origin, Age Band, Study Mode and Commencing/Continuing. Gender,
   socioeconomic status, First Nations status and home language are not filterable.
2. Native cross-filtering and active filter bar. Drill-down is a "Students in this view" table on
   Overview, Course Analysis and Demographic Breakdown. Columns: Student ID (de-identified), Risk %,
   Risk Level and the page's charted fields. Highest risk first.
3. Student List's page-level risk filter is replaced by the dashboard-wide filter of the same title.
4. A "How to filter and drill down" panel on Overview. It explains that students without an
   enrolment record are excluded once an enrolment filter is set.
5. Repairs re-point Feature-005 checks to the seven current charts, which already comply. The
   overlap check becomes per page. `test_ui.py` asserts that the Retrieve Saved button and the
   review checkbox are absent, matching Lu's `385041c`. `ui.py` is not edited.

## Open questions

None. All human-judgement decisions were answered by the product owner on 2026-10-04 (spec
Clarifications). One escalation path is pre-agreed: if the platform cannot store a default table
sort (R-3), implementation stops and asks the product owner via god.

## Risks for the reviewer to probe

- **R-2**: enrolment-field filters may not reach every widget. Fallback in plan D-2; checked at
  quickstart step 4.
- **R-3**: the JSON shapes for the global-filter page and the table sort are undocumented. They
  will be copied from a workspace export.
- **R-6**: repairs could hide a real defect. FR-022 limits the changed assertions to FR-018 –
  FR-021.

## Test plan

- 16 offline checks in the new file cover FR-001 – FR-008 and FR-010 – FR-017.
- The repaired files cover FR-018 – FR-021.
- Done-gate: `uv run pytest` shows 0 failures (base: 24 failed, 285 passed, 14 skipped), and ruff
  shows only the base I001 finding.
- Manual quickstart steps evidence the platform behaviour.
