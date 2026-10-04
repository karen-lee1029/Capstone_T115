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
| 1 | `filter_faculty` | Filter by Faculty | E | `faculty` |
| 2 | `filter_course_level` | Filter by Course Level | E | `course_level` |
| 3 | `filter_field_of_education` | Filter by Field of Education | E | `broad_primary_field_of_education` |
| 4 | `filter_origin` | Filter by Origin | E | `international_domestic` |
| 5 | `filter_age_band` | Filter by Age Band | E | `age_band` |
| 6 | `filter_study_mode` | Filter by Study Mode | E | `study_mode` |
| 7 | `filter_commencing_continuing` | Filter by Commencing/Continuing | E | `commencing_continuing` |

Query shape per widget: `datasetName` as above; fields `<dimension>` and
`<dimension>_associativity` = `COUNT_IF(\`associative_filter_predicate_group\`)`;
`disaggregated: false` (as base widget `310fbbb0`). No default selection.

Never bound to any filter widget in the dashboard (Q6): `gender`, `socioeconomic_status`,
`first_nations`, `home_language`.

**Chart selections (SDD-01)**: a click on a chart whose category is one of these four fields MUST
NOT narrow any other widget. Today only `52cb0fd3` Risk by Gender is such a chart. The mechanism,
and any resulting change to C-4 / C-5 for `52cb0fd3`, is fixed by decision Q16. Tables emit no
selections (research R-8), so table columns of these fields are display-only.

## C-2 Students in this view tables (Q7, Q9)

`widgetType: "table"`, title "Students in this view", `showDescription: true`, description
"Students matching the current filters and chart selection, highest risk first". Graph query (no
`datasetName`), `disaggregated: true`, no `filters`, no row limit, default sort `risk_pct`
descending (serialised form per research R-3). The platform renders at most 100,000 table rows; the
row cap and the wording of the description for that boundary are fixed by decision Q17 (SDD-02). Field names follow `<graph source>__<dimension>`.

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
record", and the table boundary wording fixed by Q17. MUST NOT contain "High", "Low" or "Medium" as category words.

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
| Demographic Breakdown | `drill_table_demographic` | 0 | 18 | 12 | 10 | added |
| Demographic Breakdown | `41477a60` (note) | 0 | 28 | 12 | 1 | y 18→28 |
| Demographic Breakdown | `0d5ba328` (footer) | 0 | 29 | 12 | 1 | y 19→29 |
| Student List | `310fbbb0` | — | — | — | — | removed |
| Student List | `c2d55445` (Search Student) | 0 | 2 | 12 | 2 | w 6→12 |
| Filters | `filter_*` (8) | 0 | 2·i | 12 | 2 | added, i = C-1 # |

No overlap within a page. Every other widget keeps its base position.

## C-5 Unchanged versus base `0409d7e`

`datasets`, `relationshipGraphs`, `uiSettings`; every base widget not in C-4 (compared whole); C-4
base widgets compared without `position` (`c2d55445` also without its width); the four base pages
keep name, displayName, pageType and order.

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
| `52cb0fd3` | Demographic Breakdown | Risk by Gender | y | At Risk and Not At Risk student counts for each gender |
| `292bc630` | Demographic Breakdown | Risk by Origin | y | At Risk and Not At Risk student counts for domestic and international students |
