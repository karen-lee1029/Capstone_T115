# Contract: Dashboard Interaction (Feature-006, US-29)

The repository definition `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json`
MUST satisfy every clause after Feature-006. `tests/test_dashboard_filtering.py` asserts C-1 – C-5;
the repaired `tests/test_dashboard.py` asserts C-6.

Dataset aliases: `P` = `b798cf1c` (`student_attrition_risk_prediction`); `E` = `student_enrolment`
(`Student_Enrolment_Details` in the relationship graph).

## C-1 Dashboard-wide filters (Q4, Q5, Q6, Q8)

One page: `name: "global_filters"`, `displayName: "Filters"`, `pageType: "PAGE_TYPE_GLOBAL_FILTERS"`,
appended after the four existing pages. Exactly these widgets, all `filter-multi-select`, in order:

| # | Widget name | Title | Dataset | Dimension |
|---|---|---|---|---|
| 0 | `filter_risk_level` | Filter by Risk Level | P | `risk_level` |
| 1 | `filter_course_level` | Filter by Course Level | E | `course_level` |
| 2 | `filter_field_of_education` | Filter by Field of Education | E | `broad_primary_field_of_education` |
| 3 | `filter_origin` | Filter by Origin | E | `international_domestic` |
| 4 | `filter_age_band` | Filter by Age Band | E | `age_band` |
| 5 | `filter_commencing_continuing` | Filter by Commencing/Continuing | E | `commencing_continuing` |

`filter_faculty` and `filter_study_mode` were removed by Q24: their source columns are NULL for every
student (2026-10-05 read-only check), so they could only offer "null".

Query shape per widget: `datasetName` as above; fields `<dimension>` and
`<dimension>_associativity` = `COUNT_IF(\`associative_filter_predicate_group\`)`;
`disaggregated: false` (as base widget `310fbbb0`). No default selection.

Never bound to any filter widget in the dashboard (Q6): `gender`, `socioeconomic_status`,
`first_nations`, `home_language`.

**Chart selections (SDD-01)**: a click on a chart whose category is one of these four fields MUST
NOT narrow any other widget. Today only `52cb0fd3` Risk by Gender is such a chart. Mechanism
(Q16 = a): it sits on its own canvas page `gender_breakdown` with no other data widget (C-4). Rule
checked offline: any chart whose query uses one of these four fields is the only data widget (chart,
table or counter) on its page. Tables are also selection sources (research R-8, corrected after
CODE-01). `drill_table_demographic` shows Gender beside two charts; per Q21 → Q22 it carries no
ignore setting (unavailable in this workspace) and is the only table allowed to share a page while
showing a sensitive field. Matrix row B7 must give the negative evidence; a failure goes back to the
product owner.

## C-2 Students in this view tables (Q7, Q9)

`widgetType: "table"`, title "Students in this view", `showDescription: true`, description
"Up to 100,000 students matching the current filters and chart selection, highest risk first. Narrow
the view to see others, or find any student by ID on Student List". Graph query (no
`datasetName`), `disaggregated: true`, no `filters`, no row limit, default sort `risk_pct`
descending (serialised form per research R-3), no query row cap (Q17 = a). The platform renders at
most 100,000 table rows. Field names follow `<graph source>__<dimension>`.

| Widget name | Page | Columns in order (dimension → display name) |
|---|---|---|
| `drill_table_overview` | Overview | `P.student_id` → Student ID (de-identified); `P.risk_pct` → Risk %; `P.risk_level` → Risk Level; `P.risk_score_bucket` → Risk Score Range |
| `drill_table_course` | Course Analysis | Student ID (de-identified); Risk %; Risk Level; `E.course_level` → Course Level; `E.broad_primary_field_of_education` → Field of Education |
| `drill_table_demographic` | Demographic Breakdown | Student ID (de-identified); Risk %; Risk Level; `E.age_band` → Age Band; `E.gender` → Gender; `E.international_domestic` → Origin |

The Student ID column has `useForSearch: true`, as in `163516f4`.

## C-3 How to filter and drill down panel (Q12, Q13)

Text widget `how_to_filter` on Overview; heading `How to filter and drill down` in the
`how_to_read` heading style. Body contains (case-insensitive): "Filters", "every page", "click a
bar", "active filter bar", "Students in this view", "Student ID (de-identified)", "enrolment
record", "100,000", "Gender Breakdown". MUST NOT contain "High", "Low" or "Medium" as category words.

## C-4 Layout (canvas width 12)

| Page | Widget | x | y | w | h | Change |
|---|---|---|---|---|---|---|
| Overview | `how_to_filter` | 0 | 18 | 12 | 3 | added |
| Overview | `drill_table_overview` | 0 | 21 | 12 | 10 | added |
| Overview | `3158dd73` (note) | 0 | 31 | 12 | 1 | y 18→31 |
| Overview | `98aa39b6` (footer) | 0 | 32 | 12 | 1 | y 19→32 |
| Course Analysis | `drill_table_course` | 0 | 10 | 12 | 10 | added |
| Course Analysis | `100b44c5` (note) | 0 | 20 | 12 | 1 | y 10→20 |
| Course Analysis | `3edf02b6` (footer) | 0 | 21 | 12 | 1 | y 11→21 |
| Demographic Breakdown | `521bf497` (page title) | 0 | 0 | 12 | 2 | text: subtitle "Risk distribution by age band and origin" |
| Demographic Breakdown | `292bc630` (Risk by Origin) | 0 | 10 | 12 | 8 | x 6→0, w 6→12 |
| Demographic Breakdown | `52cb0fd3` (Risk by Gender) | — | — | — | — | moved to Gender Breakdown |
| Demographic Breakdown | `drill_table_demographic` | 0 | 18 | 12 | 10 | added |
| Demographic Breakdown | `41477a60` (note) | 0 | 28 | 12 | 1 | y 18→28 |
| Demographic Breakdown | `0d5ba328` (footer) | 0 | 29 | 12 | 1 | y 19→29 |
| Gender Breakdown | `gender_title` | 0 | 0 | 12 | 2 | added: "# Gender Breakdown" + "Risk distribution by gender. Selecting a bar here does not filter other charts or tables." |
| Gender Breakdown | `52cb0fd3` (Risk by Gender) | 0 | 2 | 12 | 8 | moved here; spec and query unchanged |
| Gender Breakdown | `gender_note` | 0 | 10 | 12 | 1 | added: copy of the privacy notice of `41477a60` |
| Gender Breakdown | `gender_footer` | 0 | 11 | 12 | 1 | added: copy of the footer of `0d5ba328` |
| Student List | `310fbbb0` | — | — | — | — | removed |
| Student List | `c2d55445` (Search Student) | 0 | 2 | 12 | 2 | w 6→12 |
| Filters | `filter_*` (8) | 0 | 2·i | 12 | 2 | added, i = C-1 # |

No overlap within a page. Every other widget keeps its base position.

## C-5 Unchanged versus base `0409d7e`

`datasets`, `relationshipGraphs`, `uiSettings`; every base widget not in C-4 (compared whole); C-4
base widgets compared without `position` (`521bf497` also without its text lines); the four base
pages keep name, displayName and pageType. Page order: Overview, Course Analysis, Demographic
Breakdown, Gender Breakdown (`name: "gender_breakdown"`, `PAGE_TYPE_CANVAS`), Student List, Filters.

## C-6 Feature-005 chart checks after repair (Q3)

The repaired `CHART_CONTRACT` in `tests/test_dashboard.py` covers exactly these seven bar charts.
Each keeps At Risk `#1565C0` then Not At Risk `#42A5F5`, `natural-order` on its categorical axis,
and a shown description equal to:

| Widget | Page | Title | Categorical axis | Description |
|---|---|---|---|---|
| `5e91fa54` | Overview | Risk Level Distribution | y | Number of students in each risk category: At Risk (50% or higher) and Not At Risk (below 50%) |
| `329be35e` | Overview | Risk Score Distribution | x | Number of students in each attrition risk score range, lowest to highest; ranges from 50% are At Risk |
| `028257ed` | Course Analysis | Risk by Course Level | y | At Risk and Not At Risk student counts for each course level |
| `90548010` | Course Analysis | Risk by Field of Education | y | At Risk and Not At Risk student counts for each broad field of education |
| `eaf7eaf4` | Demographic Breakdown | Risk by Age Band | y | At Risk and Not At Risk student counts for each age band |
| `52cb0fd3` | Gender Breakdown | Risk by Gender | y | At Risk and Not At Risk student counts for each gender |
| `292bc630` | Demographic Breakdown | Risk by Origin | y | At Risk and Not At Risk student counts for domestic and international students |
