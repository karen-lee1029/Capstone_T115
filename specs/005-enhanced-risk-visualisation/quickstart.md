# Quickstart: Verifying and publishing Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Plan**: [plan.md](./plan.md) | **Contract**: [contracts/dashboard-visual-contract.md](./contracts/dashboard-visual-contract.md)

## Prerequisites

From `student_attrition_risk_app/`:

```bash
uv sync --dev
```

No workspace, credentials or network are needed for §§ 1–3. Never print or commit
`DATABRICKS_TOKEN`.

## 1. Feature checks only

```bash
uv run pytest tests/test_dashboard.py tests/test_risk_badge_visualisation.py -v
```

Expected: every offline test passes; the live `TestPredictionDataQuality` and
`TestDashboardWidgets` classes are skipped without a workspace, exactly as before.

## 2. Full suite and lint (done-gate)

```bash
uv run ruff check .
uv run pytest -q
```

Expected: ruff reports only the 4 findings that already existed before Feature-005 (`ui.py` I001 and two F401, `briefing_instructions.py` I001 — not Feature-005 lines, not fixed here); pytest reports 0 failed (260 passed and 13 skipped before Feature-005, plus the new tests). `tests/test_ui.py` is unchanged
(`git diff 9469edc -- tests/test_ui.py` is empty) and passes.

## 3. Local look at the badge (optional, mock mode)

Run the advisor page locally in mock mode, open `synthetic-student-001` (badge "At Risk" on dark
blue, white text) and `synthetic-student-002` (badge "Not At Risk" on light blue, dark text).

## 4. Publish the dashboard (product owner, in the Databricks workspace)

Agents never publish. These steps replace the workspace copy with the repository definition.

1. Check out the feature branch and locate
   `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json`.
2. Sign in to the Databricks workspace in your browser and open **Dashboards** in the left sidebar.
3. Open the existing **Student Attrition Risk Overview** dashboard. Open the kebab menu (⋮) at the
   top right and choose **Export dashboard** to keep a backup `.lvdash.json` of the current
   published version on your computer.
4. Replace the definition **in the existing dashboard**, so its id
   (`01f1b232102f1045b5d3828ffc7abc0a`) and the advisor page's **View Dashboard** link
   (`ui.py` line 46) keep working:
   - **Preferred — replace in place**: with the dashboard open in **Draft** mode, open the kebab
     menu (⋮) and choose **Replace dashboard** (shown in some workspace versions as **Import** /
     **Replace from file**), then select the repository `.lvdash.json`.
   - **Alternative — workspace file**: in **Workspace**, browse to
     `/Users/t115.capstone2026@outlook.com/`, select the existing
     `Student Attrition Risk Overview.lvdash.json`, and use its **Import** / **Replace** action to
     upload the repository file.
   - Do **not** use **Import dashboard from file** on the Dashboards list unless neither option
     exists: it creates a *new* dashboard with a new id, which breaks the advisor page link. If you
     must use it, tell the team before publishing, because the link would then need a separate,
     approved change.
5. Open the dashboard in **Draft** mode. Confirm the data warehouse is the team's usual warehouse
   and press **Refresh**; every widget loads without error.
6. Check the draft against the contract:
   - the "How to read this dashboard" panel appears directly under the title;
   - counters read **Total Students**, **At Risk**, **Not At Risk**, and At Risk + Not At Risk =
     Total Students;
   - every chart legend shows **At Risk** (dark blue) before **Not At Risk** (light blue), and no
     "High" / "Low" appears anywhere, including the **Filter by Risk Level** options and the
     **Risk Level** column of the table;
   - Risk Score Distribution runs 0-46% → 54-100% left to right;
   - every chart shows its one-line description under the title.
   If the order is not ascending, record it and stop: do not hand-edit the dashboard in the
   workspace (the repository is the source of truth).
7. Choose **Publish**, keep the existing credential setting, and confirm.
8. Open the published view and repeat the step 6 checks.

## 5. Capture evidence (product owner)

Use the browser at 100% zoom in the workspace **light** theme. Capture the page content only — no
browser chrome, no mock window frames, no dark code boxes.

1. Full page: title, "How to read this dashboard" panel and the three counters.
2. Risk Analysis row: Risk Level Distribution and Risk Score Distribution with legends and
   descriptions visible.
3. Demographic Breakdown row: the three demographic charts.
4. The **Filter by Risk Level** dropdown open, showing At Risk / Not At Risk.
5. Advisor page: one at-risk and one not-at-risk student summary showing the blue badges.

Save the images under the team's evidence folder with the date and `US-28` in each file name, and
list them in [traceability.md](./traceability.md).

## 6. Revert a teammate change (if asked)

Follow the matching entry in [teammate-changes.md](./teammate-changes.md).
