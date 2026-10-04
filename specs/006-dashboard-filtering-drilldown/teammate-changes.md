# Teammate Contribution Changes: Feature-006 (US-29)

The team approved edits to teammates' contributions needed to implement US-28 and US-29 accurately
(product owner, Feature-005 records). The product owner decided on 2026-10-04 that Feature-006
repairs the 24 base test failures (Q3) by updating the tests (Q15). Every edit is logged here with
revert steps. Revert support lives only in this document.

Status: **planned** (SDD stage). The implementation stage fills in commit SHAs and exact lines.

## TC-1 Dashboard layout (US-27)

- **File**: `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json`
- **Original author / commit**: Karen (karen-lee1029, commits as k224.lee), `946aab0`. Definition
  owner: Renny (confirmed 2026-10-01).
- **Change and reason**: remove `310fbbb0` "Filter by Risk Level" (Q8, replaced dashboard-wide);
  widen `c2d55445` w 6→12; move `3158dd73` y18→31, `98aa39b6` y19→32, `100b44c5` y10→20,
  `3edf02b6` y11→21, `41477a60` y18→28, `0d5ba328` y19→29 (room for the new widgets). Additions
  are Feature-006's own content.
- **Commit**: _at implementation_
- **Revert**: `git checkout 0409d7e -- "student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json"`
  (also removes all Feature-006 dashboard content; then remove `tests/test_dashboard_filtering.py`,
  which asserts it). Partial: re-insert `310fbbb0` from the base file at x 6, y 2, w 6, h 2 and set
  `c2d55445` back to w 6.

## TC-2 `tests/test_dashboard.py` (US-17)

- **Original author / commit**: Karen (`0bff653`, `049a3be`); Feature-005 sections by Renny.
- **Change and reason** (Q3, plan D-8): re-key `CHART_CONTRACT` and its axis map to the seven
  current charts; update `EXPECTED_WIDGET_TITLES` (drop "Filter by Risk Flag", add "Risk by Course
  Level" and "Risk by Field of Education"); make the overlap check per page.
- **Commit**: _at implementation_
- **Revert**: `git checkout 0409d7e -- student_attrition_risk_app/tests/test_dashboard.py` (the 18
  base failures return).

## TC-3 `tests/test_ui.py` (US-17)

- **Original author / commit**: Karen (`9904ec6` "Add UI test code"); two lines by Renny (`1b5225e`).
- **Change and reason** (Q3, Q15, plan D-9): match Lu's `385041c`, which commented out "Retrieve
  Saved" and the review checkbox — assert "Retrieve Saved" absent in the profile test; drop the
  checkbox block from the generate test (renamed); replace the three Retrieve Saved tests and the
  checkbox-toggle test with one absence test; update the docstring.
- **Commit**: _at implementation_
- **Revert**: `git checkout 0409d7e -- student_attrition_risk_app/tests/test_ui.py`. If Lu restores
  the button and checkbox in `ui.py`, this revert is the matching test change.
