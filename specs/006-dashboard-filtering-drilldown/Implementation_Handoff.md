# Implementation Handoff: Feature-006 — Interactive Dashboard Filtering and Drill-Down (US-29)

**For**: Codex Code Reviewer · **From**: Claude Coder · **Date**: 2026-10-04
**Branch**: `agent/claude-coder-mutdg3d2` (local commits only; base `origin/main` `0409d7e`)
**Design**: this folder — `spec.md` (Q1 – Q20), `plan.md`, `contracts/dashboard-interaction-contract.md`

## What changed

| File | Change |
|---|---|
| `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json` | **Filters** page (`PAGE_TYPE_GLOBAL_FILTERS`) with 8 multi-select filters. New **Gender Breakdown** page holding Risk by Gender (Q16 = a), with Risk by Origin widened and the Demographic subtitle updated. Student List page-level risk filter `310fbbb0` removed and Search Student widened. Three "Students in this view" tables, sorted `risk_pct` DESC through `orders`, with no row cap and the 100,000-row description (Q17 = a). "How to filter and drill down" panel on Overview. Notes and footers moved down. Datasets, relationship graph, `uiSettings` and every other widget are unchanged (checked against base). |
| `student_attrition_risk_app/tests/test_dashboard_filtering.py` (new) | 32 offline checks for FR-001 – FR-016 (one file, Q11) |
| `student_attrition_risk_app/tests/test_dashboard.py` (Karen) | Q3 repair: chart contract re-keyed to the 7 current charts (same colour, order and description rules); `EXPECTED_WIDGET_TITLES` matches the current titles; overlap check runs per page; Q20: label count 2 → 5 |
| `student_attrition_risk_app/tests/test_ui.py` (Karen) | Q3 / Q15 repair: Retrieve Saved and review checkbox asserted absent; 3 Retrieve Saved tests and the checkbox toggle test replaced by one absence test; docstring updated. `ui.py` is untouched. |
| `specs/006-dashboard-filtering-drilldown/*` | Answers Q16 – Q20, R-3 evidence, teammate changes, traceability, tasks |

No Python source, dependency or dataset change. The live check `test_has_one_page_named_overview`
(`tests/test_dashboard.py:366`) is unchanged (Q18 = a). It is skipped offline, and with workspace
access it would fail, as it already did at the base.

## Review finding dispositions

| Finding | Disposition | Where |
|---|---|---|
| SDD-01 Gender chart vs Q6 | Fixed. Q16 = a: Risk by Gender sits alone on Gender Breakdown. `test_sensitive_charts_are_isolated` and `test_gender_chart_is_on_gender_breakdown` enforce it offline. Matrix B4 (negative evidence) is pending in the workspace. | spec FR-004, contract C-1 / C-4, plan D-2a |
| SDD-02 100,000-row limit | Fixed. Q17 = a: no cap; the description and help panel state "up to 100,000", highest risk first, and how to reach others. Matrix C3 / C4 is pending in the workspace. | spec FR-012, contract C-2 / C-3 |
| SDD-03 Ineffective fallback | Fixed. Replaced by a verify-then-escalate gate. The preservation test enforces C-5 unconditionally. | plan D-2 |
| SDD-04 Acceptance gaps | Fixed. The quickstart matrix has rows A0 – D4, and a row not run is reported as pending, never as passed. | quickstart.md |
| SDD-05 Constitution check | Fixed. All 17 principles are listed. | plan.md |
| Review item 3 (live one-page test) | Q18 = a: unchanged, recorded as a known failure that appears only with workspace access | above |

## R-3 format evidence

The agent created a scratch workspace dashboard, "US29 format probe" (`01f1bfdf60b11b2188494e9fab7b0937`,
not published), through `databricks lakeview create` at the product owner's request. The server kept
the global-filter page, the filter widget and query `orders`, and dropped an unknown control key
(research R-3). The probe can be deleted; it is not part of the deliverable.

## Verification (2026-10-04, from `student_attrition_risk_app/`)

| Command | Base `0409d7e` | Now |
|---|---|---|
| `uv run pytest -q` | 24 failed, 285 passed, 14 skipped | **0 failed, 344 passed, 14 skipped** |
| `uv run pytest tests/test_dashboard_filtering.py -q` | — | 32 passed, 0 skipped (preservation checks ran against `0409d7e`) |
| `uv run ruff check .` | 1 finding (I001 `briefing_instructions.py:9`) | Same single base finding; no new finding |

Count reconciliation: 285 + 24 = 309; test_ui −4 + 1 = −3; 7 charts instead of 5 in three
parametrised Feature-005 checks = +6; new file +32 → 344.

**Mutation check** (in memory, file restored byte for byte):
- Gender chart put back on Demographic → 2 failures.
- Table `orders` removed → 1 failure.
- A filter bound to `gender` → 2 failures.

## Pending (workspace only — not claimed)

- Publishing is the product owner's job (quickstart). Every workspace acceptance matrix row (A0 – D4)
  is **pending**: filter propagation to every widget (R-2), cross-filtering, Gender isolation (B4), the
  100,000 boundary and sort-before-truncation (C4), the missing-enrolment case (D3).
- If any row fails, implementation stops and escalates via god (plan D-2). No query change is made
  without an SDD amendment.
