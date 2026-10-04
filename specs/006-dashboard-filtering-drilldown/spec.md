# Feature Specification: Feature-006 — Interactive Dashboard Filtering and Drill-Down (US-29)

**Feature Branch**: `agent/claude-coder-mutdg3d2` (decision Q14)

**Created**: 2026-10-04

**Status**: Amended after independent SDD review (SDD-01 – SDD-05); Q16 – Q19 answered; implementation in progress

**Input**: Product Backlog US-29, GitHub issue karen-lee1029/Capstone_T115 #110.

## Overview

Feature-006 is **Product Backlog US-29 — Interactive Dashboard Filtering and Drill-Down**:

> As an Academic Advisor, I want to interactively filter and drill down into student-risk
> information, so that I can focus on relevant groups of students and investigate the risk
> information displayed by the application in greater detail.
>
> **Given** student risk information is displayed in the dashboard, **when** an Academic Advisor
> applies available filters or selects a relevant dashboard view, **then** the displayed
> information updates consistently with the selected criteria and allows the advisor to examine
> the relevant student-risk information in greater detail.

US-29 is **Could Have**, 8 story points, Sprint 6, **Stretch** scope. Stretch scope on this
project is approved and required for maximum marks; it is delivered alongside, not inside, the
base-scope final application story (US-21).

### Today (origin/main `0409d7e`)

The Student Attrition Risk Overview dashboard
(`student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json`) has four
pages, created by Karen's US-27 work in `946aab0` (PR #131):

| Page | Widgets | Filters today |
|---|---|---|
| Overview | 3 counters, "How to read this dashboard" panel, Risk Level Distribution, Risk Score Distribution | none |
| Course Analysis | Risk by Course Level, Risk by Field of Education | none |
| Demographic Breakdown | Risk by Age Band, Risk by Gender, Risk by Origin | none |
| Student List | Search Student, Filter by Risk Level, Student Details table | page-level only |

An advisor can narrow information only on Student List, only by Student ID and risk level, and
cannot get from a chart to the students behind it.

The verification suite is also red at the base: **24 tests fail** (18 in `tests/test_dashboard.py`
after `946aab0`, 6 in `tests/test_ui.py` after Lu's advisor-page refactor `385041c`). The product
owner decided that Feature-006 repairs all 24 (decision Q3).

### What Feature-006 delivers

- **Dashboard-wide filters**: six filters (eight agreed in Q5; Faculty and Study Mode removed by Q24) that narrow every page at once.
- **Click-to-focus**: clicking a chart bar narrows the other widgets on that page; the selection
  shows in the active filter bar.
- **Drill-down**: a "Students in this view" table on Overview, Course Analysis and Demographic
  Breakdown, listing the students behind the current filters and selection, highest risk first.
- **Explanation**: a "How to filter and drill down" panel on Overview.
- **A green suite**: the 24 pre-existing failures repaired by updating the tests to the current,
  intended dashboard and advisor page.

Feature-006 does not change scoring, the two risk categories, the 50% threshold, the score ranges,
Feature-005's labels and colours, any dataset query, any Python source, or briefing behaviour.

## Backlog Alignment

| Backlog story | Owns | Feature-006's relationship |
|---|---|---|
| US-08, US-12 – US-15 | Backend, briefing workflow | Unchanged. |
| US-17 | Dashboard and application testing (Karen) | `tests/test_dashboard.py` and `tests/test_ui.py` are repaired to the current design (Q3, Q15). Logged in `teammate-changes.md`. |
| US-21 | Base-scope final application | Separate story. |
| US-27 | Enhanced dashboard usability and navigation (Karen, issue #108 open) | Feature-006 builds on its four-page layout on main (Q2) and adds to it. Logged. |
| US-28 | Enhanced risk visualisation (Feature-005) | Preserved. Its checks are re-pointed at the current widgets, not weakened. |
| **US-29** | Interactive filtering and drill-down | **This feature.** |

## Clarifications

### Session 2026-10-04 (product owner answers to the kickoff questions)

Answers given by the product owner in chat on 2026-10-04. Authoritative; not re-opened.

- **Q1** Which surface is "the dashboard"? → **The Lakeview dashboard only.** The advisor page gets
  no new filtering.
- **Q2** US-27 is open but its layout is on main → **Build on the current main layout.**
- **Q3** 24 tests already fail at `0409d7e` → **Fix all 24 inside Feature-006.**
- **Q4** Where do filters apply? → **Dashboard-wide: one set of filters narrows every page.**
- **Q5** Which filter fields? → **All eight: Risk Level, Faculty, Course Level, Field of Education,
  Origin (International/Domestic), Age Band, Study Mode, Commencing/Continuing.**
- **Q6** Filters on sensitive attributes (gender, socioeconomic status, First Nations status, home
  language)? → **No.** They stay in the aggregate charts and tables only.
- **Q7** Drill-down form? → **A "Students in this view" table on each analysis page**, narrowed by
  chart clicks and filters.
- **Q8** Student List's page-level "Filter by Risk Level"? → **Replace it with the dashboard-wide
  one, keeping the same title.**
- **Q9** Drill-down columns? → **Student ID (de-identified), Risk %, Risk Level, plus the fields
  charted on that page.**
- **Q10** Link from the dashboard into the advisor page? → **No.** Advisors copy the Student ID
  (Feature-005 FR-027).
- **Q11** Where do US-29 tests go? → **One new test file.** (Repairs to the 24 failing tests are
  made where those tests live, per Q3.)
- **Q12** Students without an enrolment record vanish under enrolment filters → **Accept and
  explain it on the dashboard.** *Superseded (product owner, round 3 D3, 2026-10-05): every
  student has an enrolment record (973,770 of 973,770), so the explanation is removed from the
  panel.*
- **Q13** How is filtering explained? → **A new "How to filter and drill down" panel on Overview.**
- **Q14** Folder and branch → **`specs/006-dashboard-filtering-drilldown` on
  `agent/claude-coder-mutdg3d2`.**
- **Q15** (follow-up to Q3) How to fix the 6 `test_ui.py` failures caused by Lu commenting out the
  "Retrieve Saved" button and the review checkbox in `385041c`? → **Update the tests** to match the
  simplified page. `ui.py` is not touched.

### Session 2026-10-04 (decisions after the independent SDD review)

Raised by the independent SDD review; options and evidence in `review-dispositions.md`. Answered by
the product owner in chat on 2026-10-04.

- **Q16** (SDD-01) How to stop a click on the Risk by Gender chart from narrowing other widgets →
  **a) Move Risk by Gender to its own "Gender Breakdown" page with no other data widget.**
- **Q17** (SDD-02) What the "Students in this view" tables promise given the 100,000-row rendering
  limit → **a) Up to 100,000 students, highest risk first, no extra cap; description and help panel
  say so and point to narrowing and Student List search.**
- **Q18** (review item 3) Whether to repair the live, workspace-only one-page check at
  `tests/test_dashboard.py:366` → **a) Leave it unchanged; record it as a known pre-existing failure
  that appears only with workspace access.**
- **Q20** (implementation) The three new tables each add a "Student ID (de-identified)" column, so
  Feature-005's check `test_student_id_is_labelled_de_identified` (count of that label == 2) would
  fail → **Update the count to 5** (dimension, Student Details, three new tables), keeping the check
  that a bare "Student ID" label never appears.
- **Q21** (code review CODE-01) How to stop a click in the Demographic Breakdown table from narrowing
  other widgets by Gender → **a) Test the "Ignored filters" setting, then suppress.**
- **Q22** (Q21 = a could not be carried out: the "Ignored filters" option is not offered in this
  workspace's editor, the dashboard authoring assistant could not set it, and its JSON format is
  unknown) → **a) Try the authoring assistant once; if it cannot, fall back to Q21 option b.** The
  assistant could not, so Q21 resolves to **b) observe first**: no ignore setting is added; the Demographic Breakdown table keeps Gender and the behaviour is checked in the workspace by matrix row B7. If B7 shows
  narrowing, Q6 is broken and the question returns to the product owner.
- **Q23** (workspace acceptance, 2026-10-05) Enrolment filters raise UNRESOLVED_COLUMN on every
  chart → **a) A workspace admin first checks that the Public Preview features "Cross-dataset
  filtering through relationships" and "Relationship-scoped filters" are on, then the A rows are
  re-run.**
- **Q24** (workspace acceptance) Faculty and Study Mode list only null because the source columns
  are empty → **a) with the product owner's rule: a filter that can only show "null", or that
  errors, is removed because it is not useful.** Faculty and Study Mode are removed now. Any filter
  still erroring after the Q23 preview check is removed under the same rule.
- **Q25** (Q23 = a outcome: the workspace is Databricks Free Edition, which has no Previews page,
  so relationship filter propagation cannot be enabled) What happens to the five enrolment
  filters? → **a) Add the five fields to the prediction dataset by joining in the de-duplicated
  enrolment data (one row per student), and bind the five filters to that dataset.** This is an
  approved exception to C-5 for Karen's dataset definition only; widget queries are unchanged. The
  product owner's Q24 rule (remove a filter that errors) applies only if this fails in the workspace.
- **Q26** (round 3: chart clicks fail with "Filter expression references multiple sources",
  because a chart's axis came from the enrolment dataset and its colour from the prediction
  dataset) → **a) Rebind the five Course Analysis, Demographic and Gender charts and the Course
  and Demographic "Students in this view" tables to the joined prediction columns**, adding
  `enrol_gender` for display. Every selection then uses one dataset. Student Details on Student
  List is unchanged; it is the only data widget on its page. This is a C-5 exception for Karen's
  chart queries (TC-5).
- **Q27** (round 4, B7) A click in the Demographic Breakdown table selects that student's row, so
  Risk by Age Band and Risk by Origin narrow to that one student → **a) Accept as a pass**:
  narrowing to one clicked student is not narrowing by gender, so Q6 holds.
- **Q19** (R-3) How to obtain the global-filter and table-sort JSON formats when CLI logins had
  expired → **The product owner logs in; the agent reads workspace dashboards read-only.**

### Settled from project records

- Categories "At Risk" / "Not At Risk" split at 50%; Student ID is "Student ID (de-identified)",
  the first 16 characters of the de-identified hash (Feature-005 FR-001, FR-026).
- Dashboard definition owner: Renny (confirmed 2026-10-01). The team approved edits to teammates'
  contributions needed to implement US-28 and US-29 accurately; each is logged with revert steps.
- Agents edit only the repository definition; the product owner publishes and captures light,
  professional screenshot evidence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Narrow the whole dashboard to a group of students (Priority: P1) 🎯 MVP

An Academic Advisor sets any of the six dashboard-wide filters and every counter, chart and
table on every page shows only matching students.

**Why this priority**: It is the "applies available filters ... updates consistently" half of the
criterion and the base for drill-down.

**Independent Test**: Offline, the definition has one dashboard-wide filter page with exactly the
six remaining filters (Q24), each bound to an existing dataset field, and no widget carries a fixed filter
that contradicts them (except the two category counters). In the workspace, choose one Course Level
and check every page narrows and the counters add up.

**Acceptance Scenarios**:

1. **Given** no filter is set, **When** the advisor opens any page, **Then** every widget shows all
   students, as today.
2. **Given** values are selected in one or more filters, **When** the advisor opens any page,
   **Then** every counter, chart and table shows only students matching all selected filters.
3. **Given** any selection, **When** the advisor reads the Overview counters, **Then** Total = At
   Risk + Not At Risk.
4. **Given** Risk Level is set to "Not At Risk", **When** the advisor reads the At Risk counter,
   **Then** it shows 0.
5. **Given** filters are set, **When** the advisor clears them, **Then** every widget returns to all
   students.

---

### User Story 2 - Click a chart to focus the page (Priority: P2)

An Academic Advisor clicks a bar (for example the "At Risk" segment of one course level) and the
other widgets on that page narrow to that group; the selection appears in the active filter bar
and can be cleared.

**Why this priority**: It is the "selects a relevant dashboard view" interaction; it depends on the
widgets sharing one dataset graph.

**Independent Test**: Offline, every chart and table on each canvas page queries the same
relationship graph. In the workspace, click a bar and see the page's table and other chart narrow.

**Acceptance Scenarios**:

1. **Given** an analysis page, **When** the advisor clicks a bar, **Then** the other charts and the
   "Students in this view" table on that page show only that group.
2. **Given** a chart selection, **When** the advisor looks at the active filter bar, **Then** the
   selection is listed and can be removed.
3. **Given** a chart selection and dashboard-wide filters, **When** the advisor reads the page,
   **Then** widgets show students matching both.

---

### User Story 3 - Drill down to the individual students (Priority: P3)

From Overview, Course Analysis or Demographic Breakdown, the advisor sees the students behind the
current filters and selection, highest risk first, and can copy a Student ID into the advisor page.

**Independent Test**: Offline, each of the three pages has one "Students in this view" table with
the agreed columns, Student ID first, sorted by Risk % descending.

**Acceptance Scenarios**:

1. **Given** one of the three pages, **When** the advisor looks below the charts, **Then** a
   "Students in this view" table lists the matching students.
2. **Given** the table, **When** it first shows, **Then** rows are ordered by Risk % highest first.
3. **Given** a row, **When** the advisor reads it, **Then** it shows Student ID (de-identified),
   Risk %, Risk Level and the page's charted fields with Feature-005's labels.
4. **Given** a Student ID from the table, **When** pasted into the advisor page, **Then** the student
   is found (Feature-005 FR-027; not re-tested).

---

### User Story 4 - Understand the interactions (Priority: P4)

The advisor learns how to filter and drill down from the dashboard itself.

**Independent Test**: Offline, Overview holds a "How to filter and drill down" panel with the
required content.

**Acceptance Scenarios**:

1. **Given** Overview, **When** the advisor reads the panel, **Then** it explains the filters,
   clicking a bar, the active filter bar and the students tables.

---

### User Story 5 - A trustworthy, green verification suite (Priority: P5)

The product owner and reviewers can rely on the test suite: the 24 tests that fail at the base are
repaired to describe the current dashboard and advisor page, without weakening what they protect.

**Independent Test**: `uv run pytest` passes with 0 failures; the repaired dashboard checks still
assert Feature-005's colours, order and descriptions, now on all seven current charts.

**Acceptance Scenarios**:

1. **Given** the repaired `tests/test_dashboard.py`, **When** it runs, **Then** its Feature-005
   checks cover every bar chart in the current definition (seven) with the same colour, order and
   description rules.
2. **Given** the repaired overlap check, **When** it runs, **Then** it checks overlap within each
   page, not across pages.
3. **Given** the repaired `tests/test_ui.py`, **When** it runs, **Then** it asserts the simplified
   advisor page: no "Retrieve Saved" button and no review checkbox, while every other assertion
   (Generate, Regenerate, metadata, download) is unchanged.
4. **Given** the publish and evidence steps, **When** the product owner follows the quickstart,
   **Then** the dashboard is published and each scenario above is evidenced.

### Edge Cases

- **No students match**: counters 0, charts show no data, tables empty; no error; clearing restores.
- **Risk Level filter excludes a counter's category**: that counter shows 0.
- **Student without an enrolment record**: included with no enrolment filter set; excluded once
  Course Level, Field of Education, Origin, Age Band or Commencing/Continuing is filtered (Q12). Explained in the panel.
- **~974,000 students**: the platform renders at most 100,000 rows in a table (Databricks
  dashboard limits). A table shows the 100,000 highest-risk students of a broad view and says so;
  the advisor narrows or searches to reach others (Q17 = a).
- **Search Student plus filters**: Search Student stays page-level on Student List; a student
  outside the filters is not shown.
- **A dashboard-wide filter does not narrow some widget** (platform risk R-2): implementation stops
  that check, records the widget and escalates via god (plan D-2). No query change is made without
  an approved SDD amendment.
- **Clicking a bar of a sensitive attribute** (Risk by Gender): MUST NOT narrow any other widget or
  table (FR-004). Risk by Gender is alone on its own page (Q16 = a).
- **Workspace unreachable in tests**: all Feature-006 checks are offline; the existing live
  dashboard check keeps its skip behaviour.

## Requirements *(mandatory)*

### Functional Requirements

#### Dashboard-wide filters

- **FR-001**: The dashboard MUST provide one dashboard-wide filter page whose filters apply to every
  page (Q4).
- **FR-002**: The dashboard-wide filters MUST be exactly six, multi-select, defaulting to all
  values, titled: "Filter by Risk Level", "Filter by Course Level", "Filter by Field of Education", "Filter by Origin", "Filter by Age Band", "Filter by Commencing/Continuing" (Q5, Q8; Faculty and Study Mode removed by Q24 because their source
  columns are empty).
- **FR-003**: Each filter MUST be bound to the prediction dataset, to a named dimension or a
  column its source query provides (Q25); Risk Level MUST offer only "At Risk" and "Not At Risk".
- **FR-003a** (Q25): The prediction dataset's source MUST read the prediction table and LEFT JOIN
  the enrolment record chosen by the same rule as the enrolment dataset (latest census date, then
  enrolment year), keeping one row per student. It adds only `enrol_course_level`,
  `enrol_field_of_education`, `enrol_origin`, `enrol_age_band` and `enrol_commencing_continuing`,
  plus `enrol_gender` for display only (Q26). No other sensitive field is added, and no filter may
  bind to `enrol_gender` (FR-004).
- **FR-004**: No interaction path MUST narrow any widget by gender, socioeconomic status, First
  Nations status or home language (Q6). This covers (a) filter widgets — none may be bound to these
  fields — and (b) selections — a click on a chart or table showing one of these fields MUST NOT
  narrow any other widget to a group defined by that field. Selecting one student's row in a table
  may narrow the page to that one student (Q27). Charts: Risk by Gender sits alone on a "Gender Breakdown" page (Q16 = a).
  Tables: tables are cross-filter sources on the platform (research R-8, corrected after code review
  CODE-01). The Student List table is alone on its page. The mechanism for the Demographic Breakdown
  table, which shows Gender (Q9), is **observe first** (Q21 → Q22): no ignore setting is added
  (the platform option is unavailable here), and matrix row B7 must show that a click in that table
  never narrows Risk by Age Band or Risk by Origin to a gender group. Narrowing them to the one
  selected student is allowed (Q27). B7 passed in round 4.
- **FR-005**: Every counter, chart and table MUST respond to the dashboard-wide filters. No widget
  may carry a fixed filter on a filtered field, except the At Risk and Not At Risk counters on
  Risk Level.
- **FR-006**: The Student List page-level "Filter by Risk Level" MUST be removed; "Search Student"
  MUST remain (Q8).
- **FR-007**: Filters MUST apply immediately on selection (no Apply step), as today.

#### Click-to-focus

- **FR-008**: On each canvas page, every chart and table MUST query the same relationship graph so
  a selection on a chart of an allowed field can filter the other widgets on that page. **Q26**: on
  the analysis pages, every field MUST come from the prediction dataset, so a selection never spans
  two datasets.
- **FR-009**: Feature-006 MUST NOT disable cross-filtering for charts of allowed fields or the
  active filter bar. Sensitive-field charts follow FR-004(b).

#### Drill-down

- **FR-010**: Overview, Course Analysis and Demographic Breakdown MUST each include one table
  titled "Students in this view" (Q7).
- **FR-011**: Columns, in order: Student ID (de-identified), Risk %, Risk Level, then the page's
  charted fields — Overview: Risk Score Range; Course Analysis: Course Level, Field of Education;
  Demographic Breakdown: Age Band, Gender, Origin (Q9).
- **FR-012**: Each table MUST default to Risk % descending and MUST NOT set a query row cap (Q17 = a).
  Its description MUST say it shows up to 100,000 students in the view, highest risk first, and how
  to reach others (narrow with filters or a chart selection; find a student by ID on Student List).
  The 100,000 limit is the platform's rendering limit; the structural check is not proof that every
  student is reachable, and the boundary is evidenced by matrix row C4.
- **FR-013**: Student ID MUST be the existing 16-character `student_id` dimension; no identifier or
  field is added to any dataset.

#### Explanation

- **FR-014**: Overview MUST include a text panel titled "How to filter and drill down" explaining
  the dashboard-wide filters, clicking a bar, the active filter bar, the "Students in this view"
  tables (Q13; the missing-enrolment sentence was removed in round 3 because no such student
  exists).
- **FR-015**: The panel MUST use Feature-005's category names and "Student ID (de-identified)".

#### Preservation

- **FR-016**: Feature-006 MUST NOT change datasets, the relationship graph, `uiSettings`, chart
  colour maps, axis order, chart titles or descriptions, the "How to read this dashboard" panel,
  any Python source, or briefing behaviour.
- **FR-017**: No two widgets on the same page may overlap.

#### Repair of the pre-existing failures (Q3, Q15)

- **FR-018**: `tests/test_dashboard.py` MUST be updated so that its Feature-005 repository checks
  target the seven current bar charts by their current widget names (`5e91fa54`, `329be35e`,
  `028257ed`, `90548010`, `eaf7eaf4`, `52cb0fd3`, `292bc630`) with their current descriptions and
  categorical axes; the colour, natural-order and description rules MUST stay as strict as before.
- **FR-019**: `EXPECTED_WIDGET_TITLES` in `tests/test_dashboard.py` MUST list the titles of the
  current design: drop "Filter by Risk Flag" (removed in `946aab0`), add "Risk by Course Level" and
  "Risk by Field of Education", keep "Filter by Risk Level" and "Search Student".
- **FR-020**: The overlap check in `tests/test_dashboard.py` MUST compare widgets within each page.
- **FR-020a** (Q20): `test_student_id_is_labelled_de_identified` MUST expect 5 occurrences of the
  "Student ID (de-identified)" label; its bare-"Student ID" assertion is unchanged.
- **FR-021**: `tests/test_ui.py` MUST be updated to the simplified advisor page: the profile test
  asserts "Retrieve Saved" is **absent**; the generate test drops its review-checkbox assertion;
  the three Retrieve Saved tests and the checkbox-toggle test are replaced by one test asserting
  that neither the "Retrieve Saved" button nor the review checkbox is rendered. No other assertion
  changes. `ui.py` is not edited (Q15).
- **FR-022**: Repairs MUST NOT delete or loosen any assertion other than those named in FR-018 –
  FR-021 and FR-020a.

#### Verification

- **FR-023**: All US-29 checks MUST be offline and live in one new file,
  `tests/test_dashboard_filtering.py` (Q11). It verifies FR-001 – FR-008, FR-010 – FR-017.
- **FR-024**: After Feature-006, `uv run pytest` MUST report 0 failures, and ruff MUST show no
  finding beyond the one at the base (I001 in `briefing_instructions.py`, outside scope).

#### Publishing, records, traceability

- **FR-025**: The quickstart MUST give steps to replace and publish the dashboard and capture
  evidence for each acceptance scenario.
- **FR-026**: Every change to a teammate's contribution MUST be logged in `teammate-changes.md`
  (file and lines, original author and commit, change and reason, commit, revert steps).
- **FR-027**: `traceability.md` MUST map every FR to its automated check or manual step.

### Key Entities

- **Dashboard-wide filter**: named multi-select control bound to one dataset field; all pages.
- **Chart selection**: transient cross-filter from a chart click; one page.
- **Students in this view table**: student-level table per analysis page.
- **Teammate change record**: one entry per changed teammate contribution with revert steps.

## Success Criteria *(mandatory)*

- **SC-001**: 6 of 6 filters (Q24: Faculty and Study Mode removed) exist and narrow 100% of counters, charts and tables on all 5 canvas pages (Overview, Course Analysis, Demographic Breakdown, Gender Breakdown, Student List).
- **SC-002**: For any selection, Total = At Risk + Not At Risk on Overview.
- **SC-003**: 3 of 3 analysis pages have a "Students in this view" table sorted by Risk % descending.
- **SC-004**: From any chart bar of an allowed field, the advisor reaches its students in at most 2 clicks.
- **SC-005**: 0 filters on gender, socioeconomic status, First Nations status or home language.
- **SC-006**: `uv run pytest` 0 failures (base: 24); 0 new ruff findings.
- **SC-007**: 7 of 7 bar charts covered by the repaired Feature-005 checks.
- **SC-008**: 100% of changed teammate contributions logged with revert steps.
- **SC-009**: Published dashboard matches the repository definition, evidenced by screenshots.

## Assumptions

- The platform provides dashboard-wide filters, cross-filtering and an active filter bar
  (Databricks "Use dashboard filters" docs; research R-1). Exact serialised shapes are confirmed
  from a workspace export during implementation (R-3).
- Enrolment-field filters narrow prediction-dataset widgets through the existing many-to-one
  relationship (R-2); verified in the workspace by the product owner (quickstart matrix); if not,
  escalation per plan D-2.
- Lu's removal of "Retrieve Saved" and the review checkbox in `385041c` is intended (Q15).
- US-27's layout at `0409d7e` is the current design (Q2).

## Dependencies

- **US-27 layout** (Karen, `946aab0`), **Karen's `test_dashboard.py` and `test_ui.py`**, **Lu's
  `385041c`** — edited or matched with team approval; logged.
- **Feature-005** — labels, colours, Student ID; preserved.
- **The product owner** — publishes and captures evidence.

## Out of Scope

- The advisor page (Q1) and any dashboard-to-app link (Q10); `ui.py` is not edited (Q15).
- Drill-through to Student List (Q7 chose per-page tables).
- New datasets, dimensions, measures, chart types or charts; an "Unknown" enrolment bucket (Q12).
- The base ruff finding in `briefing_instructions.py`.
- Scoring, categories, threshold, score ranges, colours, labels, briefing behaviour.
- Publishing by an agent; push, PR or merge.
