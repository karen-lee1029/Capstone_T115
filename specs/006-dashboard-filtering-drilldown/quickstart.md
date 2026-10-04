# Quickstart: Feature-006 (US-29)

## Developers — verify offline

From `student_attrition_risk_app/`:

```bash
uv sync --dev
uv run ruff check .                                   # only the base I001 finding
uv run pytest tests/test_dashboard_filtering.py -q
uv run pytest -q                                      # 0 failures (base had 24)
```

## Product owner — publish and evidence

Agents never publish. Use a light theme for screenshots.

1. In the Databricks workspace, open *Student Attrition Risk Overview* → ⋮ → **Replace dashboard**
   (or **Import** and replace) with the repository file
   `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json`.
2. **Publish** and open the published view.
3. **Filters present**: open the filter panel; confirm the eight filters (Risk Level, Faculty,
   Course Level, Field of Education, Origin, Age Band, Study Mode, Commencing/Continuing) and none
   on gender, socioeconomic status, First Nations status or home language. Screenshot (US1).
4. **Filters reach every widget (R-2)**: select one Faculty value. On Overview the counters drop
   and Total = At Risk + Not At Risk. Visit every page and confirm each widget narrows. If any does
   not, stop and report it (plan D-2). Screenshot Overview.
5. **Risk Level filter**: set "Not At Risk"; the At Risk counter shows 0. Screenshot.
6. **Clear filters**: everything returns.
7. **Click-to-focus**: on Course Analysis click the At Risk segment of one course level; the other
   chart and the "Students in this view" table narrow; the selection shows in the active filter
   bar. Screenshot (US2).
8. **Drill-down**: the table shows Student ID (de-identified), Risk %, Risk Level and the page's
   fields, highest Risk % first. Paste one Student ID into the advisor page and retrieve the
   student. Screenshot both (US3).
9. **Explanation**: screenshot the "How to filter and drill down" panel (US4).
10. **Empty combination**: pick filters with no students; 0 / no data, no error.
11. Store the screenshots with the US-29 evidence.
