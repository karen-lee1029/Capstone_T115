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
| A0 | Check the page list (Overview, Course Analysis, Demographic Breakdown, Gender Breakdown, Student List); open the filter panel | Exactly 6 filters (Risk Level, Course Level, Field of Education, Origin, Age Band, Commencing/Continuing; Faculty and Study Mode removed by Q24); none for gender, socioeconomic status, First Nations status, home language |
| A1 | Risk Level = "Not At Risk" | At Risk counter 0; each of the 5 canvas pages, Gender Breakdown included, shows only Not At Risk students |
| A2 | Course Level = one value | Counters drop and add up; every chart and table on all 5 canvas pages (Overview, Course Analysis, Demographic Breakdown, Gender Breakdown, Student List) narrows. Record each page separately |
| A3 | Removed (was Course Level; now A2). Faculty removed by Q24 | — |
| A4 | Field of Education = one value | As A2 |
| A5 | Origin = one value | As A2 |
| A6 | Age Band = one value | As A2 |
| A7 | Removed: Study Mode removed by Q24 | — |
| A8 | Commencing/Continuing = one value | As A2 |
| A9 | Two values in one filter (e.g. two age bands) | Union of the two; counters add up |
| A10 | Course Level = one value AND Age Band = one value | Intersection: counts ≤ each single-filter count (A2, A6) |
| A11 | Clear all filters | Every widget returns to the cleared-state counts |

If any widget in A1 – A10 does not narrow: stop, record widget/field/observation, escalate via god
(plan D-2). Do not continue to the evidence step for that row.

### B — Chart selection (US2; FR-004(b), FR-008, FR-009)

| Row | Steps | Expected |
|---|---|---|
| B1 | Course Analysis: click the At Risk segment of one course level | Field of Education chart and the "Students in this view" table narrow; selection shows in the active filter bar |
| B2 | Keep B1, then set Course Level = one value | Widgets show the intersection of the selection and the filter |
| B3 | Remove the chart selection from the active filter bar, then clear Course Level | Each removal restores the previous state independently |
| B4 | Gender Breakdown: click a bar of Risk by Gender, then visit every other page | **No other widget or table narrows** (negative evidence for Q6) |
| B5 | Demographic Breakdown: click one Age Band bar, then one Origin bar | Other allowed charts and the table narrow; clearing restores |
| B6 | Overview: click one Risk Score Range bar | Counters, Risk Level chart and the table narrow |
| B7 | Demographic Breakdown: click a Gender cell (and a Gender column value) in the "Students in this view" table | **Risk by Age Band and Risk by Origin never narrow by gender**. A row click may narrow them to that one student (Q27) (negative evidence for Q6; no suppression setting is applied, per Q21 → Q22). **Pass**: each chart shows either all students or only the one selected student. **Fail, stop and escalate**: either chart narrows to a gender group (more than the one selected student). Then confirm Age Band and Origin bar clicks still narrow the table |

### C — Drill-down tables (US3; FR-010 – FR-013)

| Row | Steps | Expected |
|---|---|---|
| C1 | On each of Overview, Course Analysis, Demographic Breakdown, read the table | Columns per contract C-2; Risk % highest first |
| C2 | Copy one Student ID into the advisor page | Student found (Feature-005 FR-027) |
| C3 | Choose a narrow cohort (< 100,000 students; note its counter value) | The table reaches the end of the cohort (scroll to the last row); where the platform shows a row count it equals the counter value |
| C4 | Cleared state (about 974,000 students, > 100,000) | Description says up to 100,000; rows run from the highest Risk % down; narrowing to < 100,000 shows the whole cohort; a student outside the table is found via Search Student |

### D — Other cases (edge cases; FR-014)

| Row | Steps | Expected |
|---|---|---|
| D1 | Student List: Search Student = a student, then set a Course Level that excludes them | Student not shown; clearing Course Level shows them again |
| D2 | Pick filters with no students | Counters 0, charts no data, tables empty, no error |
| D3 | Missing enrolment: find a Student ID with no enrolment record (product owner's read-only query: prediction rows without a matching enrolment hash). With no filter set, search it on Student List; then set any enrolment filter | Shown with no filter; gone once an enrolment filter is set. If no such student exists, record "no case in data" and mark D3 not applicable |
| D4 | Read the "How to filter and drill down" panel | Explains filters, clicking a bar, active filter bar, tables, the 100,000 boundary and the Gender Breakdown page |

## Completion report

The implementation handoff lists every row as **passed (evidence)**, **failed (escalated)**,
**pending (not run)** or **not applicable (reason)**.

### Re-test after Q25 (round 3)

Re-publish from the Q25 commit. Then re-run A2 – A10, B2, B5 – B7, C3, C4 and D1 – D3. Record each
row as pass, fail or pending, never as assumed. Chart clicks that only highlight (B5, B6, the second
half of B7) may persist; Q25 does not change how charts query.

### Re-test after Q26 (round 4, completed; all passed or accepted)

Re-publish from the Q26 commit. Re-run B1, B2, B3, B5 and B7: no "multiple sources" error, and the
other widgets on the page narrow. For B7, use the pass and fail rule in row B7: narrowing to the one
selected student passes (Q27), and narrowing to a gender group fails. Also run C4 with **all filters cleared**, searching on
Student List for an ID ranked below the top 100,000 (example: `64e9c59460e17c3a`, Risk % 49.7,
613,371 students rank above it).
