# Quickstart: Feature-006 (US-29)

## Developers — verify offline

From `student_attrition_risk_app/`:

```bash
uv sync --dev
uv run ruff check .                                   # only the base I001 finding
uv run pytest tests/test_dashboard_filtering.py -q
uv run pytest -q                                      # 0 failures (base had 24)
```

Report whether the preservation checks ran or were skipped (they need git and base commit
`0409d7e`).

**Offline checks prove structure only.** Behaviour on the platform is proved only by the
workspace acceptance matrix below. Any row not run, or run without the needed data, is reported as
**pending**, never as passed (Constitution XV).

## Product owner — publish

Agents never publish. Use a light theme for screenshots.

1. In the Databricks workspace, open *Student Attrition Risk Overview* → ⋮ → **Replace dashboard**
   (or **Import** and replace) with
   `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json`.
2. **Publish** and open the published view. Start every row from a cleared state (all filters All,
   no chart selection) unless the row says otherwise.

## Workspace acceptance matrix

Evidence = screenshot named `US29-<row>.png`, plus the observed counts written in the evidence
log. "Counters add up" = Total = At Risk + Not At Risk.

### A — Dashboard-wide filters (US1; FR-001 – FR-007; R-2 gate, plan D-2)

| Row | Steps | Expected |
|---|---|---|
| A0 | Open the filter panel | Exactly 8 filters (Risk Level, Faculty, Course Level, Field of Education, Origin, Age Band, Study Mode, Commencing/Continuing); none for gender, socioeconomic status, First Nations status, home language |
| A1 | Risk Level = "Not At Risk" | At Risk counter 0; every page shows only Not At Risk students |
| A2 | Faculty = one value | Counters drop and add up; every chart and table on all 4 pages narrows |
| A3 | Course Level = one value | As A2 |
| A4 | Field of Education = one value | As A2 |
| A5 | Origin = one value | As A2 |
| A6 | Age Band = one value | As A2 |
| A7 | Study Mode = one value | As A2 |
| A8 | Commencing/Continuing = one value | As A2 |
| A9 | Two values in one filter (e.g. two faculties) | Union of the two; counters add up |
| A10 | Faculty = one value AND Course Level = one value | Intersection: counts ≤ each single-filter count (A2, A3) |
| A11 | Clear all filters | Every widget returns to the cleared-state counts |

If any widget in A1 – A10 does not narrow: stop, record widget/field/observation, escalate via god
(plan D-2). Do not continue to the evidence step for that row.

### B — Chart selection (US2; FR-004(b), FR-008, FR-009)

| Row | Steps | Expected |
|---|---|---|
| B1 | Course Analysis: click the At Risk segment of one course level | Field of Education chart and the "Students in this view" table narrow; selection shows in the active filter bar |
| B2 | Keep B1, then set Faculty = one value | Widgets show the intersection of the selection and the filter |
| B3 | Remove the chart selection from the active filter bar, then clear Faculty | Each removal restores the previous state independently |
| B4 | Click a bar of Risk by Gender (wherever Q16 places it) | **No other widget or table narrows** (negative evidence for Q6) |
| B5 | Demographic Breakdown: click one Age Band bar, then one Origin bar | Other allowed charts and the table narrow; clearing restores |
| B6 | Overview: click one Risk Score Range bar | Counters, Risk Level chart and the table narrow |

### C — Drill-down tables (US3; FR-010 – FR-013)

| Row | Steps | Expected |
|---|---|---|
| C1 | On each of Overview, Course Analysis, Demographic Breakdown, read the table | Columns per contract C-2; Risk % highest first |
| C2 | Copy one Student ID into the advisor page | Student found (Feature-005 FR-027) |
| C3 | Choose a narrow cohort (< 100,000 students; note its counter value) | The table reaches the end of the cohort (scroll to the last row); where the platform shows a row count it equals the counter value |
| C4 | Cleared state (about 974,000 students, > 100,000) | Behaviour matches decision Q17: the stated boundary is shown, rows are the highest Risk % first, and the documented way to reach other students works |

### D — Other cases (edge cases; FR-014)

| Row | Steps | Expected |
|---|---|---|
| D1 | Student List: Search Student = a student, then set a Faculty that excludes them | Student not shown; clearing Faculty shows them again |
| D2 | Pick filters with no students | Counters 0, charts no data, tables empty, no error |
| D3 | Missing enrolment: find a Student ID with no enrolment record (product owner's read-only query: prediction rows without a matching enrolment hash). With no filter set, search it on Student List; then set any enrolment filter | Shown with no filter; gone once an enrolment filter is set. If no such student exists, record "no case in data" and mark D3 not applicable |
| D4 | Read the "How to filter and drill down" panel | Explains filters, clicking a bar, active filter bar, tables, missing-enrolment exclusion and the Q17 boundary |

## Completion report

The implementation handoff lists every row as **passed (evidence)**, **failed (escalated)**,
**pending (not run)** or **not applicable (reason)**.
