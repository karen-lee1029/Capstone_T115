# Implementation Plan: Feature-006 — Interactive Dashboard Filtering and Drill-Down (US-29)

**Branch**: `agent/claude-coder-mutdg3d2` | **Date**: 2026-10-04 | **Spec**: [spec.md](./spec.md) | **Contract**: [contracts/dashboard-interaction-contract.md](./contracts/dashboard-interaction-contract.md)

**Base commit**: `origin/main` `0409d7e`

## Summary

Two parts. (1) **US-29**: in the repository dashboard definition, add one dashboard-wide filter
page with six multi-select (eight before Q24) filters, remove the now-duplicated Student List risk filter, add a
"Students in this view" table to three pages, add a "How to filter and drill down" panel, and move
footers down. (2) **Repair (Q3, Q15)**: update Karen's `tests/test_dashboard.py` and
`tests/test_ui.py` so the 24 base failures describe the current, intended design. US-29 checks go
in one new test file. No dataset, Python source or dependency changes.

## Technical Context

**Language/Version**: Python 3.11; Databricks AI/BI (Lakeview) dashboard JSON (dataset config 1.1,
widget spec versions 2–3).

**Primary Dependencies**: pytest, Streamlit `AppTest`, stdlib `json` — existing; none added.

**Storage**: None.

**Testing**: pytest offline. New file parses the repository JSON; preservation checks read the base
definition with `git show 0409d7e:<path>` and skip if git or the commit is unavailable. Ruff
`E, F, I, UP`, line length 110.

**Target Platform**: Databricks workspace (published by the product owner).

**Constraints**: Change map only. No Python source. Offline tests. Agents never publish. Every
teammate edit logged.

**Scale/Scope**: Dashboard: +1 page, +6 filters (8 before Q24), +3 tables, +1 panel, −1 filter, 1 widget widened,
6 note/footer widgets moved. Tests: 1 new file; 2 teammate test files repaired.

### Baseline (measured 2026-10-04 at `0409d7e`)

`uv run pytest`: **24 failed, 285 passed, 14 skipped**. `uv run ruff check .`: 1 finding (I001,
`src/student_attrition_risk/briefing_instructions.py:9`, out of scope).

| Failing tests | Count | Cause | Repair |
|---|---|---|---|
| `test_dashboard.py::TestRepositoryDashboardDefinition::test_chart_colour_map_matches_contract[*]`, `test_chart_categorical_axis_natural_order[*]`, `test_chart_description_shown[*]` | 15 | `CHART_CONTRACT` names five pre-US-27 widgets (`chart_risk_donut`, `chart_risk_by_faculty`, `chart_risk_study_mode`, `chart_risk_gender`, `chart_risk_intl`) that no longer exist | D-8 |
| `…::test_every_bar_chart_is_in_contract` | 1 | Same contract vs seven current charts | D-8 |
| `…::test_all_expected_widget_titles_present` | 1 | Expects "Filter by Risk Flag", removed in `946aab0` | D-8 |
| `…::test_layout_has_no_overlapping_widgets` | 1 | Treats all pages as one canvas (`7e33b19c` vs `2b28df60` are page titles on different pages) | D-8 |
| `test_ui.py::test_at_risk_student_shows_profile_with_briefing_actions`, `test_generate_briefing_displays_text_metadata_checkbox_and_download`, `test_retrieve_saved_displays_stored_briefing`, `test_retrieve_saved_no_briefing_shows_info`, `test_retrieve_saved_error_shows_error`, `test_review_checkbox_can_be_toggled` | 6 | `385041c` commented out "Retrieve Saved" and the review checkbox | D-9 |

Checked: all seven current bar charts already use At Risk `#1565C0` / Not At Risk `#42A5F5`,
`natural-order` on their categorical axis, and a shown description — so the repair re-points the
checks without changing the dashboard's charts.

## Constitution Check

| Principle | How this plan satisfies it |
|---|---|
| I Specification-driven | Every edit traces to an FR; the product owner's 15 answers are in spec Clarifications. |
| II Strict scope | Dashboard JSON, one new test file, two repaired test files (Q3), this folder. No `src/` change. |
| III Read broadly, write narrowly | Discovery read datasets, 4 pages, both failing test files, `385041c`, wireframes. |
| IV Minimal change | Reuses existing dimensions; repairs change only the assertions named in FR-018 – FR-021. |
| V Reuse architecture | Platform filters, cross-filtering and tables; existing JSON conventions. |
| VI No unnecessary complexity | No drill-through, parameters or custom SQL. |
| VII Plan-defined structure | All changes sit in the files of the Change map, in the existing `dashboard/` and `tests/` layout; no new module, package or directory. |
| VIII Technology compatibility | Lakeview-native widget types only. |
| IX Separation of responsibilities | Filtering, selection and table rendering stay the platform's job; datasets keep data shaping; tests stay offline structure checks. No Python layer is added. |
| X Security and privacy | No new identifier; no interaction path narrows by a sensitive attribute — filters and chart selections (FR-004, Q6, Q16). |
| XI Input validation and errors | No new input crosses an application boundary: filter values come from dataset dimensions and the platform handles empty selections. Error paths are the platform's own (empty result = 0 / no data, edge cases). No custom validation layer is needed. |
| XII Proportionate testing | Offline structure checks per FR; platform behaviour evidenced manually. |
| XIII Human review | Codex SDD and code reviews; product owner publishes. |
| XIV Traceability | `traceability.md`. |
| XV Completion means specification satisfaction | Done requires offline checks green, full suite 0 failures, and every quickstart matrix row either evidenced or explicitly reported as pending (workspace-only). Offline green alone is not reported as acceptance. |
| XVI Preserve team contributions | Edits to Karen's layout and tests are team-approved for US-29, minimal, and logged with revert steps. Lu's `ui.py` is untouched. |
| XVII Human-controlled VCS | Local commits only. |

## Change map

| File | Change | FRs |
|---|---|---|
| `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json` | Filter page + 6 filters (Q24); Gender Breakdown page (D-2a); remove `310fbbb0`; widen `c2d55445`; 3 tables; panel; layout per C-4 | FR-001 – FR-017 |
| `student_attrition_risk_app/tests/test_dashboard_filtering.py` (new) | US-29 offline checks | FR-023 |
| `student_attrition_risk_app/tests/test_dashboard.py` (Karen) | Repair per D-8 | FR-018 – FR-020, FR-022 |
| `student_attrition_risk_app/tests/test_ui.py` (Karen) | Repair per D-9 | FR-021, FR-022 |
| `specs/006-dashboard-filtering-drilldown/*` | SDD, records | FR-025 – FR-027 |

## Design

### D-1 Dashboard-wide filter page

One page `global_filters`, `displayName: "Filters"`, `pageType: "PAGE_TYPE_GLOBAL_FILTERS"`,
holding six `filter-multi-select` widgets (contract C-1). Each widget's query mirrors base widget
`310fbbb0`: `datasetName`, the field, and `<field>_associativity` =
`COUNT_IF(\`associative_filter_predicate_group\`)`, `disaggregated: false`. Risk Level queries the
prediction dataset `b798cf1c`; the seven enrolment filters query `student_enrolment`.

### D-2 Filter reach across datasets — verification and escalation gate (R-2, SDD-03)

All eleven existing data widgets (three counters, seven bar charts, Student Details) already query
through the relationship graph (no `datasetName`), and the new tables do too. There is therefore no
"switch to graph style" fallback; the earlier fallback is withdrawn (SDD-03).

Gate: the product owner runs quickstart matrix rows A1 – A9 in the workspace. If every widget
narrows, record that as evidence. If any widget does not narrow, implementation **stops** for that
row, records the widget, field and observation in the implementation handoff, and escalates via god.
No query, dataset or widget change beyond C-4 is made without an approved SDD amendment, so C-5
(preservation) stays unconditional. Until the row passes, its acceptance is reported as pending.

**Outcome (2026-10-05)**: the gate fired. Enrolment-bound filters raised UNRESOLVED_COLUMN on every
chart; relationship filter propagation is a Public Preview that Free Edition cannot enable (Q23).
The approved amendment is Q25 = a: P's source joins in the five enrolment fields and the filters
bind to P (contract C-1, C-5 exception, teammate change TC-4). This is evidenced offline by the
Risk Level filter, already bound to P, which narrowed every widget in the workspace (B1).

### D-2a Sensitive chart isolation (Q16 = a, SDD-01)

Add canvas page `gender_breakdown` ("Gender Breakdown") after Demographic Breakdown. Move widget
`52cb0fd3` Risk by Gender there with its spec and query unchanged, plus a title text, a privacy note
and a footer (contract C-4). On Demographic Breakdown, widen Risk by Origin to w 12 and drop "gender"
from the page subtitle. Cross-filters act only within a page (research R-8), so a Gender selection
has no other widget to narrow. Global filters still apply to the chart. Matrix row B4 is the
negative evidence.

### D-3 Student List risk filter (Q8)

Remove `310fbbb0`. The dashboard-wide Risk Level filter uses the same title. Widen `c2d55445`
"Search Student" from w 6 to w 12.

### D-4 Students in this view tables (Q7, Q9)

Three `table` widgets (`drill_table_overview`, `drill_table_course`, `drill_table_demographic`),
graph-style queries like `163516f4`, `disaggregated: true`, columns per contract C-2, default sort
`risk_pct` descending, no row limit, no fixed filters. No existing widget serialises a table sort,
so its shape comes from a workspace export (R-3). If the platform cannot store a default table
sort, stop and escalate to the product owner via god; do not decide. The platform renders at most
100,000 table rows (rendering limit, not a query limit); the table's completeness contract, its
description says "up to 100,000", highest risk first, and how to reach others (Q17 = a); no query
row cap.

### D-5 Explanation panel (Q13)

Text widget `how_to_filter` on Overview in the `how_to_read` style; content per contract C-3.

### D-6 Layout

Positions per contract C-4: new widgets below existing charts; note and footer moved down; nothing
else moves.

### D-7 Unchanged

`datasets`, `relationshipGraphs`, `uiSettings` (`applyModeEnabled: false` gives FR-007), and every
existing widget except `310fbbb0` (removed), `c2d55445` (width) and six note/footer widgets (y).

### D-8 Repair `tests/test_dashboard.py` (Q3)

- Re-key `CHART_CONTRACT` (descriptions) and its categorical-axis map to the seven current widget
  names, with each chart's description and categorical axis as they are at `0409d7e`
  (contract C-6). Keep the colour, natural-order and description assertions unchanged.
- `EXPECTED_WIDGET_TITLES` per FR-019. This set is also used by the live (skipped) workspace check;
  the same update applies.
- `test_layout_has_no_overlapping_widgets`: group layout items by page before the pairwise check.
- `test_student_id_is_labelled_de_identified`: expected label count 2 → 5 (Q20, FR-020a).
- No other test, constant or replica changes (FR-022).

### D-9 Repair `tests/test_ui.py` (Q15)

- `test_at_risk_student_shows_profile_with_briefing_actions`: `assert "Retrieve Saved" not in
  _button_labels(at)`; other assertions unchanged.
- `test_generate_briefing_displays_text_metadata_checkbox_and_download`: remove the review-checkbox
  block; rename to `test_generate_briefing_displays_text_metadata_and_download`.
- Replace the three `test_retrieve_saved_*` tests and `test_review_checkbox_can_be_toggled` with one
  `test_retrieve_saved_and_review_checkbox_are_not_rendered`: after generating a briefing for an
  at-risk student, no "Retrieve Saved" button and no checkbox labelled "I have reviewed this
  AI-generated briefing".
- Update the module docstring line that lists "Retrieve Saved" and "review checkbox".
- Retrieval itself stays covered at service level by Feature-002 tests (unchanged).

## Test plan

### New file `tests/test_dashboard_filtering.py` (US-29)

| Check | FR |
|---|---|
| Exactly one `PAGE_TYPE_GLOBAL_FILTERS` page | FR-001 |
| Its widgets are exactly the 8 contract filters, multi-select, contract titles and order | FR-002 |
| Each filter field resolves to a dimension of the dataset it queries | FR-003 |
| Risk Level filter field is the `risk_level` dimension (two-category rule is Feature-005's, not re-tested) | FR-003 |
| No filter widget anywhere bound to `gender`, `socioeconomic_status`, `first_nations`, `home_language` | FR-004(a) |
| Any chart whose query uses one of those four fields is the only data widget on its page; `52cb0fd3` is on `gender_breakdown` | FR-004(b) |
| No widget query has a fixed filter on a filtered field except `counter_high`/`counter_low` on `risk_level` | FR-005 |
| `310fbbb0` absent; "Search Student" present on Student List at w 12 | FR-006 |
| `uiSettings.applyModeEnabled` is false | FR-007, FR-009 |
| On every canvas page, chart and table queries have no `datasetName` (graph queries) | FR-008 |
| Each of the 3 pages has exactly one "Students in this view" table | FR-010 |
| Table columns match contract C-2 in order | FR-011 |
| Table default sort `risk_pct` descending; no row cap; description per contract C-2 | FR-012 |
| Student ID column is the `student_id` dimension | FR-013 |
| `how_to_filter` on Overview contains contract phrases; no "High"/"Low"/"Medium" | FR-014, FR-015 |
| Datasets, relationship graph, uiSettings and untouched widgets equal base (`git show`) | FR-016 |
| No overlap within any page — covered by the repaired per-page check in `test_dashboard.py` (FR-020), not duplicated | FR-017 |

### Repaired files

Full `uv run pytest` = 0 failures; ruff no new finding (FR-024). Manual: quickstart.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R-2 | A dashboard-wide filter does not reach a widget | D-2 gate: evidence or stop-and-escalate; no unapproved query change |
| R-7 | Sensitive chart selection narrows other widgets | FR-004(b); mechanism per Q16; matrix row B4 negative evidence |
| R-8 | Table shows only 100,000 rows of a broad selection | Contract per Q17; matrix row C4 with a > 100,000 cohort |
| R-3 | Global-filter page / table sort JSON shape undocumented | Copy from a workspace export before editing; escalate if sort cannot be stored |
| R-4 | Students without enrolment records vanish under enrolment filters | Accepted and explained (Q12) |
| R-6 | Repairs mask a real defect | FR-022; reviewer confirms each changed assertion maps to FR-018 – FR-021 |
