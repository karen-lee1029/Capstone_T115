# Research: Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Date**: 2026-10-01 | **Plan**: [plan.md](./plan.md)

No Technical Context item was left as NEEDS CLARIFICATION. The product owner's nine decisions are
recorded in the spec's Clarifications; the decisions below settle the implementation choices the
spec leaves to planning.

## R1 — Where to rename the categories

- **Decision**: Rename at the `risk_level` dimension of dataset `b798cf1c`
  (`CASE WHEN source.attrition_risk_percentage >= 50 THEN 'At Risk' ELSE 'Not At Risk' END`), then
  update every literal that repeats the old value: the two counter filter expressions, the two
  counter titles and the `value` of every colour-map entry on the five charts. The filter widget
  `filter_risk_level` and the table's "Risk Level" column read the dimension, so they pick up the
  new values with no edit.
- **Rationale**: The dimension is the single definition of the category (spec FR-001). Renaming
  there keeps the 50% split identical and keeps the dimension name `risk_level` (and every field
  reference to it) stable, so no query, relationship or filter dataset changes.
- **Alternatives rejected**: renaming the dimension itself (touches every field expression); a new
  "label" dimension beside `risk_level` (two definitions of one category — Principle VI); keeping
  "High" / "Low" and relabelling only titles (legends and filters would still show the old names,
  failing FR-002).
- **Widget names** (`counter_high`, `counter_low`, `chart_risk_by_faculty`,
  `chart_risk_study_mode`, `chart_risk_donut`) are internal ids not shown to advisors. They are not
  renamed (Principle IV); tests locate widgets by these ids.

## R2 — Enforcing order

- **Decision**: Add `"sort": {"by": "natural-order"}` to the categorical `scale` of all five charts
  (the `x` axis of Risk Score Distribution; the `y` axis of Risk Level Distribution, Risk by Age
  Band, Risk by Gender and Risk by Origin), and list the "At Risk" colour mapping before "Not At
  Risk" in all five colour maps.
- **Rationale**: Natural (ascending label) order gives exactly the required orders with the current
  labels: the eight range labels `0-46%`, `46-48%`, `48-49%`, `49-50%`, `50-51%`, `51-52%`,
  `52-54%`, `54-100%` are already in ascending order as text, and "At Risk" sorts before "Not At
  Risk". Making the order explicit stops the platform's default (which may sort by bar value)
  from reordering ranges or categories when the data changes (spec Edge Cases). One rule on every
  axis is the "single documented order" the spec requires (FR-011).
- **Verification**: the offline checks assert the sort setting and that the eight labels, sorted as
  text, equal their ascending numeric order — so a future label change that breaks text order
  fails a test. The product owner confirms the rendered order when publishing (quickstart § 4).
- **Alternatives rejected**: renaming ranges with numeric prefixes such as `1: 0-46%` (changes the
  approved labels and the dimension, FR-010); a custom sort dimension (new dataset field —
  Principle VI).

## R3 — Explanations

- **Decision**: (a) One new text widget, `how_to_read`, using the same `multilineTextboxSpec` and
  light inline style as the existing `synthetic_notice` widget, placed full width directly under
  the page title (`y = 2`, height 3), with every widget at `y >= 2` moved down by 3. (b) Each of
  the five charts gets `showDescription: true` and a one-line `description.value`; the two
  existing descriptions are reworded to name the categories. Exact text: contract §§ 4–5.
- **Rationale**: Reuses the dashboard's existing text-widget and description patterns
  (Principle V). The panel sits where an advisor starts reading (spec US2 scenario 4). Moving the
  rest down keeps the grid free of overlaps without reshaping any other widget.
- **Style**: light background, dark text, the two category blues as small swatches — no dark
  boxes (the project's evidence style).
- **Alternatives rejected**: a second dashboard page (advisors would miss it); explanation inside
  each chart title (titles become long and inconsistent).

## R4 — Dashboard verification (`tests/test_dashboard.py`, Karen's file, approved edit)

- **Decision**:
  1. Update the existing replicas to the new labels: `RISK_LEVEL_THRESHOLD` comment,
     `EXPECTED_WIDGET_TITLES` (`At Risk`, `Not At Risk` in place of `High Risk`, `Low Risk`),
     `_risk_level` and its docstring, the `TestRiskLevelClassification` assertions, and the
     wording of the live data-quality docstrings and messages. Test names and the live
     `TestDashboardWidgets` class stay as they are.
  2. Append one offline class, `TestRepositoryDashboardDefinition`, that loads
     `dashboard/Student Attrition Risk Overview.lvdash.json` relative to the test file (no
     workspace) and checks: the `risk_level` expression yields only `'At Risk'` / `'Not At Risk'`
     at `>= 50`; no `'High'`, `'Low'` or `'Medium'` category literal remains; both counters' titles
     and filters; every chart colour map equals the contract map in contract order; every chart's
     categorical axis has natural-order sort; the bucket labels are in ascending order; every
     chart shows a non-empty description; the `how_to_read` widget text contains both labels,
     `50%` and both colours; every title in `EXPECTED_WIDGET_TITLES` is present; no two widgets
     overlap on the grid.
- **Title forms**: `filter_faculty` stores its title as a plain string (`"Filter by Risk Flag"`)
  while the others use `{"value": ...}`. The offline title collector accepts both forms; the JSON
  is not normalised (Principle IV).
- **Rationale**: The approved edit keeps all dashboard checks in the file the team already owns for
  them, and the offline class makes them run in every suite run — the live class is skipped
  without workspace access.

## R5 — Badge verification (`tests/test_risk_badge_visualisation.py`, new)

- **Decision**: Three tests.
  1. Parametrised over the at-risk (`synthetic-student-001`) and not-at-risk
     (`synthetic-student-002`) mock students: render the page with `AppTest`, load the student,
     and assert the summary markdown contains the expected badge class wrapping the expected label,
     and that no `st.info` / `st.success` / `st.warning` element is rendered.
  2. From the rendered `<style>` markdown, parse the `.risk-badge` and `.not-risk-badge` rules and
     assert `background` = `#1565C0` / `#42A5F5` and `color` = `#FFFFFF` / `#172033`.
  3. Compute the WCAG 2.x contrast ratio of each parsed text/background pair and assert it is at
     least 4.5.
- **Text colours**: `#FFFFFF` on `#1565C0` = 5.75:1; `#172033` on `#42A5F5` = 6.15:1. White on
  `#42A5F5` is only 2.65:1, so the light badge needs dark text; `#172033` is the page's existing
  heading colour (`.student-reference`), so no new colour is introduced.
- **Service double**: a local minimal fake (`get_student_profile` from `MockStudentRepository`;
  `has_stored_briefing` / `get_stored_briefing` returning nothing), patched in through
  `student_attrition_risk.main.build_service` with `st.cache_resource.clear()`, as
  `tests/test_defect_resolution.py` does. `tests/test_ui.py` is not imported or edited.
- **Not re-tested**: the presence of the words "At Risk" / "Not At Risk" alone (already in
  `test_ui.py`) — test 1 asserts the class/label pairing, which is new.

## R6 — Things deliberately left unchanged

- The advisor page's `.risk-circle` (red score ring) — not part of the badge decision; recorded in
  the spec's Out of Scope.
- The counters' existing font colours already match their category blues (`counter_high`
  `#1565C0`, `counter_low` `#42A5F5`) — no edit needed (FR-007 already holds).
- `uiSettings.theme.visualizationColors` — only used for series without an explicit mapping; every
  risk chart has an explicit mapping.
- The table description, section headers, privacy notice and "last updated" text.
