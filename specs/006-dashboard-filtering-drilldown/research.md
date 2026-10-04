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

**Decision**: Confirm the shapes against the workspace before editing.

**Evidence (2026-10-04, Q19)**: None of the six workspace dashboards used a global filter or a table
sort. At the product owner's request the agent created a scratch dashboard, "US29 format probe"
(`01f1bfdf60b11b2188494e9fab7b0937`, `/Users/t115.capstone2026@outlook.com/US29 format probe.lvdash.json`),
with the Lakeview API (`databricks lakeview create`). It held a `PAGE_TYPE_GLOBAL_FILTERS` page with a
`filter-multi-select` widget, a table whose query had `"orders": [{"direction": "DESC", "expression": ...}]`,
and a control table whose query had an unknown key. The server accepted the dashboard, kept the
global-filter page, the filter widget and `orders` exactly, and **dropped the unknown key**. So the
server validates query keys, and `orders` is a recognised field. These are the shapes used. The
probe is not published and is not part of the deliverable.

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

## R-8 Platform interaction limits (added after the SDD review)

- **Cross-filter scope**: a click on a chart filters the other widgets **on the same page** that
  share the dataset (graph) ([Use dashboard filters](https://docs.databricks.com/aws/en/dashboards/manage/filters/)).
- **Which widgets emit selections**: click-to-filter works for bar, box plot, heatmap, histogram,
  pie, scatter and point-map visualisations; table widgets do not emit cross-filters (Databricks
  community article "Cross-filtering for AI/BI dashboards",
  https://community.databricks.com/t5/community-articles/cross-filtering-for-ai-bi-dashboards/td-p/82912).
  No documented per-widget switch to turn cross-filtering off was found. To be confirmed from the
  workspace export (R-3).
- **Rendering limits**: tables render up to 100,000 rows before truncation; bar and other charts
  render up to 10,000 rows. For datasets over 100,000 rows the query runs on the backend
  ([Dashboard limits](https://docs.databricks.com/aws/en/dashboards/limits)). Whether truncation
  applies after the table's sort is to be confirmed in the workspace (matrix row C4).

Consequences: the Gender **column** in a table cannot narrow anything; the Risk by **Gender** bar
chart can narrow the other widgets on its page (SDD-01, Q16); a broad selection (unfiltered, about
974,000 students) cannot be shown in full in one table (SDD-02, Q17).
