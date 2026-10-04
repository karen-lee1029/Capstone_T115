# Research: Feature-006 (US-29)

## R-1 Platform interaction features

**Decision**: Use the Databricks AI/BI (Lakeview) dashboard's native dashboard-wide (global)
filters, cross-filtering and active filter bar.

**Rationale**: Databricks documents global filters that apply across all pages, page-level
filters, cross-filtering (click a data point to filter others on the same page), drill-through,
and an active filter bar listing every filter not set to All and every cross-filter
([Use dashboard filters](https://docs.databricks.com/aws/en/dashboards/manage/filters/)).

**Alternatives rejected**: parameters with custom SQL (dataset change, FR-016); filtering in the
advisor page (Q1).

## R-2 Filter reach across the two datasets

**Finding**: `relationshipGraphs[0]` joins P to E many-to-one on `student_deidentified_hash`
(definition lines 174–192). Charts and the Student Details table query through the graph; the base
filters query P directly.

**Decision**: Bind enrolment filters to E; rely on the relationship to narrow graph widgets.
Verified in the workspace (quickstart step 4); fallback in plan D-2.

## R-3 Serialised form of new elements

**Finding**: The base definition has no global-filter page and no table default sort (no `orders`
or `limit` keys; only chart-axis `sort`). Public docs do not show the serialised global-filter page.

**Decision**: Before editing, copy the exact shapes from a workspace export of a scratch dashboard
with one global filter and one table sorted descending. The contract fixes names, titles, fields,
columns and positions, which the tests check. If a default table sort cannot be stored, escalate.

## R-4 Students without an enrolment record

**Decision (Q12)**: Accept their exclusion under enrolment filters and explain it in the panel. No
data change. The count may be measured by the product owner with a read-only query and noted in
evidence; it does not change the design.

## R-5 Filter fields

**Decision (Q5, Q6)**: Eight filters — Risk Level (P) and Faculty, Course Level, Field of
Education, Origin, Age Band, Study Mode, Commencing/Continuing (E). Gender, socioeconomic status,
First Nations status and home language are not filterable (Constitution X, lines 132–136).
Evidence for the base set: high-fidelity wireframe "Find a Student" (Student ID, Risk Level,
Faculty), `docs/High Fidelity Wireframes/High fidelity databricks.docx`.

## R-6 Drill-down approach

**Decision (Q7)**: Per-page "Students in this view" tables driven by filters and cross-filtering.
Drill-through rejected by the product owner.

## R-7 Base failures and their cause

**Finding** (`uv run pytest` at `0409d7e`: 24 failed, 285 passed, 14 skipped):

- 18 in `tests/test_dashboard.py`: Feature-005 checks name five pre-US-27 widgets; the title set
  expects "Filter by Risk Flag" (removed by `946aab0`); the overlap check compares widgets across
  pages. All seven current bar charts already satisfy Feature-005's colour, order and description
  rules, so the dashboard itself is compliant.
- 6 in `tests/test_ui.py`: Lu's `385041c` commented out the "Retrieve Saved" button and the review
  checkbox in `ui.py` (around lines 792 and 880).

**Decision (Q3, Q15)**: Repair the tests to the current design (plan D-8, D-9); do not edit `ui.py`.
