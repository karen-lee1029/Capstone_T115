# Teammate Contribution Changes: Feature-006 (US-29)

The team approved edits to teammates' contributions needed to implement US-28 and US-29 accurately
(product owner, Feature-005 records). The product owner decided on 2026-10-04 that Feature-006
repairs the 24 base test failures (Q3) by updating the tests (Q15). Every edit is logged here with
revert steps. Revert support lives only in this document.

Status: **implemented** in the Feature-006 implementation commit on `agent/claude-coder-mutdg3d2`
(the commit that adds `tests/test_dashboard_filtering.py`; find it with
`git log --oneline -- student_attrition_risk_app/tests/test_dashboard_filtering.py`).

## TC-1 Dashboard layout (US-27)

- **File**: `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json`
- **Original author / commit**: Karen (karen-lee1029, commits as k224.lee), `946aab0`. Definition
  owner: Renny (confirmed 2026-10-01).
- **Change and reason**: remove `310fbbb0` "Filter by Risk Level" (Q8, replaced dashboard-wide);
  widen `c2d55445` w 6→12; move `3158dd73` y18→31, `98aa39b6` y19→32, `100b44c5` y10→20,
  `3edf02b6` y11→21, `41477a60` y18→28, `0d5ba328` y19→29 (room for the new widgets). Q16 = a:
  move `52cb0fd3` Risk by Gender from Demographic Breakdown (x 0, y 10, w 6, h 8) to the new Gender
  Breakdown page (x 0, y 2, w 12, h 8); widen `292bc630` Risk by Origin (x 6 → 0, w 6 → 12); change
  `521bf497`'s subtitle from "Risk distribution by age band, gender and origin" to "Risk
  distribution by age band and origin". Additions are Feature-006's own content.
- **Commit**: the Feature-006 implementation commit (see Status)
- **Revert**: `git checkout 0409d7e -- "student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json"`
  (also removes all Feature-006 dashboard content; then remove `tests/test_dashboard_filtering.py`,
  which asserts it). Partial: re-insert `310fbbb0` from the base file at x 6, y 2, w 6, h 2 and set
  `c2d55445` back to w 6. To undo only the Gender move, delete the `gender_breakdown` page, put
  `52cb0fd3` back on Demographic Breakdown at x 0, y 10, w 6, h 8, set `292bc630` to x 6, w 6 and
  restore `521bf497`'s subtitle.

## TC-2 `tests/test_dashboard.py` (US-17)

- **Original author / commit**: Karen (`0bff653`, `049a3be`); Feature-005 sections by Renny.
- **Change and reason** (Q3, plan D-8): re-key `CHART_CONTRACT` and its axis map to the seven
  current charts; update `EXPECTED_WIDGET_TITLES` (drop "Filter by Risk Flag", add "Risk by Course
  Level" and "Risk by Field of Education"); make the overlap check per page.
- **Commit**: the Feature-006 implementation commit (see Status)
- **Revert**: `git checkout 0409d7e -- student_attrition_risk_app/tests/test_dashboard.py` (the 18
  base failures return). Also (Q20) `test_student_id_is_labelled_de_identified` count 2 → 5;
  revert by setting it back to 2 together with removing the three US-29 tables.

## TC-3 `tests/test_ui.py` (US-17)

- **Original author / commit**: Karen (`9904ec6` "Add UI test code"); two lines by Renny (`1b5225e`).
- **Change and reason** (Q3, Q15, plan D-9): match Lu's `385041c`, which commented out "Retrieve
  Saved" and the review checkbox — assert "Retrieve Saved" absent in the profile test; drop the
  checkbox block from the generate test (renamed); replace the three Retrieve Saved tests and the
  checkbox-toggle test with one absence test; update the docstring.
- **Commit**: the Feature-006 implementation commit (see Status)
- **Revert**: `git checkout 0409d7e -- student_attrition_risk_app/tests/test_ui.py`. If Lu restores
  the button and checkbox in `ui.py`, this revert is the matching test change.

## TC-4 Prediction dataset `b798cf1c` source and `tests/test_dashboard.py::test_prediction_dataset_source_table` (US-17)

- **Original author / commit**: Karen (dashboard dataset and its test).
- **Change and reason** (Q25 = a): `config.source` changes from the prediction table name to a
  query. The query reads that table (`p.*`) and LEFT JOINs the de-duplicated enrolment record plus
  course, adding five `enrol_*` filter columns. Dimensions, measures and every widget query are
  unchanged. The test now asserts that the source reads `FROM <prediction table> p` instead of
  equalling the table name.
- **Commit**: the Q25 commit (see Implementation_Handoff.md).
- **Revert**: set `config.source` back to
  `workspace.student_aggregate.student_attrition_risk_prediction`, restore the test assertion
  `config.get("source") == PREDICTION_TABLE`, and rebind the five filters to `student_enrolment`.
  Note: that binding errors on Databricks Free Edition.

## TC-5 Charts `028257ed`, `90548010`, `eaf7eaf4`, `292bc630`, `52cb0fd3` (US-17 / US-28)

- **Original author / commit**: Karen (dashboard charts).
- **Change and reason** (Q26 = a): each chart's enrolment field is renamed from
  `Student_Enrolment_Details.<dim>` to the joined prediction column
  `student_attrition_risk_prediction.enrol_<dim>` (Course Level, Field of Education, Age Band,
  Origin, Gender). A click previously selected values from two datasets, and the platform rejected
  it ("Filter expression references multiple sources"). Titles, colours, axes, sort and descriptions
  are unchanged. The joined source gains `enrol_gender`, for display only. Karen's tests needed no
  change.
- **Commit**: the Q26 commit (see Implementation_Handoff.md).
- **Revert**: in each chart, rename the fields back (`student_attrition_risk_prediction__enrol_<dim>`
  → `Student_Enrolment_Details__<dim>`, with the matching expressions), and drop `enrol_gender` from
  the prediction source. Chart clicks then error again on Free Edition.
