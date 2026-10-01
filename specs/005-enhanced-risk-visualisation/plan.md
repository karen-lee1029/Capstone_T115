# Implementation Plan: Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Branch**: `feat/feature-005-enhanced-risk-visualisation` | **Date**: 2026-10-01 | **Spec**: [spec.md](./spec.md) | **Contract**: [contracts/dashboard-visual-contract.md](./contracts/dashboard-visual-contract.md)

**Input**: Feature specification from `specs/005-enhanced-risk-visualisation/spec.md`

## Summary

Make the two risk surfaces speak one visual language with the smallest possible edits to files
that already exist. In the repository dashboard definition, rename the obsolete "High" / "Low"
categories to "At Risk" / "Not At Risk" at their single source (the `risk_level` dimension) and at
every place that repeats the literal (two counter filters, two counter titles, five colour maps);
put "At Risk" first in every colour map; set an explicit natural (ascending) order on every
chart's categorical axis; add a description to every chart; and add one "How to read this
dashboard" text widget. On the advisor page, change four colour values in the two badge CSS rules,
and (decision 10, added 2026-10-01) recolour the relative-risk score ring to the category blues.
Verify with offline checks added to Karen's approved `tests/test_dashboard.py` and one new
`tests/test_risk_badge_visualisation.py`. No Python source logic, dataset query (beyond the two
category literals), score range, module, dependency or abstraction is added or changed.

## Technical Context

**Language/Version**: Python 3.11 (`pyproject.toml` `target-version = "py311"`); Databricks
Lakeview dashboard JSON (`.lvdash.json`; dataset config version 1.1; widget spec versions 2–3).

**Primary Dependencies**: Streamlit (advisor page), pytest, Streamlit `AppTest`, Python `json` /
`re` stdlib — all existing; none added.

**Storage**: None. The dashboard reads `workspace.student_aggregate.student_attrition_risk_prediction`
unchanged.

**Testing**: pytest, offline. Dashboard checks parse the repository JSON with `json.load`; badge
checks render `src/student_attrition_risk/ui.py` with `AppTest` and a local fake service built on
`MockStudentRepository`, patched in through `student_attrition_risk.main.build_service` as
`tests/test_defect_resolution.py` does (that file is not edited). Ruff (`E, F, I, UP`, line
length 110).

**Target Platform**: Databricks workspace (Lakeview dashboard, published by the product owner) and
Databricks App (advisor page); local mock mode for verification.

**Project Type**: Web service + Streamlit app in `student_attrition_risk_app/`, plus a Lakeview
dashboard definition in `student_attrition_risk_app/dashboard/`.

**Performance Goals**: None. Presentation only.

**Constraints**: Change only the four approved files plus this feature's documents (spec FR-020);
`tests/test_ui.py` and every other merged test unchanged (FR-017); offline verification (FR-018);
no Streamlit alert widgets (FR-009); agents never publish to the workspace (spec Clarifications);
every teammate edit recorded in [teammate-changes.md](./teammate-changes.md) (FR-022). Baseline: 260 passed / 13 skipped / 0 failed; ruff has 4 pre-existing findings outside Feature-005's lines (3 in `ui.py`, 1 in `briefing_instructions.py`) that stay unfixed — done-gate is "no new finding".

**Scale/Scope**: 1 dashboard JSON (2 datasets; 18 widgets → 19), 2 CSS rules, 1 updated test file,
1 new test file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — still passing.*

| Principle | How this plan satisfies it |
|---|---|
| I Specification-driven | Every edit traces to an FR in spec.md; the nine product-owner decisions are recorded in its Clarifications before any change. |
| **II Strict scope containment** | Only four files change (§ Change map). No `src/` logic, no dataset query beyond the two `risk_level` literals, no briefing module (`briefing_provider.py`, `briefing_instructions.py`, `briefing_validation.py`), no US-27 / US-29 work. `tests/test_ui.py` and every other merged test are read-only. |
| III Read broadly, write narrowly | `ui.py`, `test_ui.py`, `models.py`, `student_repository.py`, `test_defect_resolution.py` and the dashboard JSON were read to confirm label wording, flag logic, test patterns and ownership; only change-map lines are written. |
| **IV Minimal necessary change** | The rename is made at the dimension that defines the category plus the literals that must repeat it. The 8 score ranges, counter colours, table, filter datasets and every other widget property stay as they are; the only layout change is one inserted row. The badge change is four colour values; the score ring (decision 10) changes two colour values, adds one modifier rule and one class variable. |
| **V Reuse and extend** | Reuses the dashboard's existing blues, its existing `multilineTextboxSpec` text-widget pattern (as in `synthetic_notice`), each chart's existing `frame.description` slot, the existing `.risk-badge` / `.not-risk-badge` classes and badge logic, `MockStudentRepository`, and the `AppTest` + patched `build_service` approach already in `tests/test_defect_resolution.py`. |
| VI No unnecessary complexity | No new module, helper package, conftest, fixture framework, dependency or dashboard page. |
| VII Plan-defined structure | File list and line ranges are fixed here; tasks may not widen them. |
| VIII Technology compatibility | Stays within Lakeview JSON and Streamlit; Python test code only. |
| IX Separation of responsibilities | Dashboard presentation stays in the dashboard definition; badge presentation stays in the page CSS; flag logic (`ui.py:649-654`) and the backend are untouched. |
| X Security and privacy | No identifiers, data or credentials are added. Tests are offline; `DATABRICKS_TOKEN` is never read, printed or committed. |
| XI Input validation and error handling | No new input boundary. The offline checks fail loudly if the JSON is malformed. |
| **XII Proportionate testing** | One offline check per visual rule (labels, colours, order, explanations) in the dashboard file; three badge tests. Nothing `test_ui.py` already covers (badge wording present) or the existing derived-column tests cover is re-tested. |
| XIII Human review | The product owner reviews the JSON diff, publishes the dashboard and inspects the screenshots before merge. |
| XIV Traceability | FR → task → check recorded in `traceability.md` (Track E); teammate edits in `teammate-changes.md`. |
| XV Completion = spec | Done when FR-001–FR-026 hold and the dashboard is published; nothing extra. |
| **XVI Preserve team contributions** | Two teammate contributions change (plus the dashboard definition, owned by Renny (the user), confirmed 2026-10-01), each explicitly approved by the team for US-28 (spec Clarifications) and each recorded in `teammate-changes.md` with exact revert instructions. Karen's `test_ui.py` is untouched; badge tests go in a new file rather than hers. |
| **XVII Human-controlled version control** | Agents commit only to `feat/feature-005-enhanced-risk-visualisation`, as instructed; no push, merge, PR or change to `main`. Publishing to the workspace is the product owner's action. |

No violations; Complexity Tracking is empty.

## Change map

JSON line numbers are as of `9469edc`; Python line numbers as of the branch base. Paths are
relative to `student_attrition_risk_app/`. Exact target values are in
[contracts/dashboard-visual-contract.md](./contracts/dashboard-visual-contract.md).

| Track | File | Lines | Change |
|---|---|---|---|
| **B** | `dashboard/Student Attrition Risk Overview.lvdash.json` | 15 | `risk_level` dimension `CASE`: `'High'` → `'At Risk'`, `'Low'` → `'Not At Risk'`. |
| B | same | 302, 314 (`counter_high`) | Filter `IN ('High')` → `IN ('At Risk')`; title `High Risk` → `At Risk`. Widget `name` unchanged. |
| B | same | 362, 374 (`counter_low`) | Filter `IN ('Low')` → `IN ('Not At Risk')`; title `Low Risk` → `Not At Risk`. |
| B | same | 459-468, 548-557, 731-740, 813-822, 895-904 (colour maps of `chart_risk_donut`, `chart_risk_by_faculty`, `chart_risk_study_mode`, `chart_risk_gender`, `chart_risk_intl`) | Mapping values `High` → `At Risk` (`#1565C0`, first), `Low` → `Not At Risk` (`#42A5F5`, second). |
| B | same | the categorical `scale` of each of the five charts (`y` for the four horizontal bar charts, `x` for Risk Score Distribution) | Add `"sort": {"by": "natural-order"}` (research R2). |
| B | same | `frame` of the five charts (430-440, 512-522, 702-706, 784-788, 866-870) | `showDescription: true`; description text per contract § 4 (two existing descriptions reworded, three added). |
| B | same | `pages[0].layout` | Insert widget `how_to_read` at `{x: 0, y: 2, width: 12, height: 3}`; add 3 to the `y` of every other widget whose `y >= 2`. Content per contract § 5. |
| **C** | `src/student_attrition_risk/ui.py` | 144-145 (`.risk-badge`) | `background: #fee4e2` → `#1565C0`; `color: #b42318` → `#FFFFFF`. |
| C | same | 155-156 (`.not-risk-badge`) | `background: #dcfae6` → `#42A5F5`; `color: #067647` → `#172033`. |
| C (decision 10) | same | 181, 187 (`.risk-circle`); new 193-196; new 660-664; 702 (line numbers as of `46b4965`) | Ring `border` and `color` `#d92d20` → `#1565C0`; new `.risk-circle.not-risk-circle` rule (`#42A5F5` ring, `#172033` text); `circle_class` chosen from `attrition_risk_flag`; score `<div>` uses it (contract § 7a). No other line of `ui.py` changes. |
| C | `tests/test_risk_badge_visualisation.py` | NEW | Badge render, colour and contrast checks (research R5). |
| **D** | `tests/test_dashboard.py` | 26, 39-52, 59-61, 86-108, 262-279 | `RISK_LEVEL_THRESHOLD` comment; `EXPECTED_WIDGET_TITLES` (`High Risk` / `Low Risk` → `At Risk` / `Not At Risk`); `_risk_level` replica and its asserted values; data-quality docstrings and messages. Test function names unchanged. |
| D | same | append after line 353 | New class `TestRepositoryDashboardDefinition` — offline checks of the repository JSON (research R4). The live `TestDashboardWidgets` class is unchanged. |
| **E** | `specs/005-enhanced-risk-visualisation/traceability.md` (NEW), `teammate-changes.md`, `quickstart.md` | — | Traceability record; fill the "pending" commit hashes; confirm publish steps against the final JSON. |

**Cross-track overlap**: none between B and C (disjoint files), so they run in parallel. D asserts
against the JSON that B produces, so D runs after B. E runs after B, C and D.

## Project Structure

### Documentation (this feature)

```text
specs/005-enhanced-risk-visualisation/
├── spec.md
├── plan.md                           # this file
├── research.md
├── data-model.md
├── quickstart.md                     # verification + product-owner publish steps
├── contracts/
│   └── dashboard-visual-contract.md  # label map, colour map, order, text widgets, badge
├── checklists/requirements.md
├── teammate-changes.md               # one revert-ready entry per teammate contribution changed
├── tasks.md                          # /speckit-tasks
└── traceability.md                   # Track E (created during implementation)
```

### Source Code (repository root)

```text
student_attrition_risk_app/
├── dashboard/
│   └── Student Attrition Risk Overview.lvdash.json   # Track B
├── src/student_attrition_risk/
│   └── ui.py                                         # Track C — badge rules + score ring (decision 10)
└── tests/
    ├── test_dashboard.py                             # Track D — approved edit (Karen)
    ├── test_risk_badge_visualisation.py              # Track C — NEW
    └── test_ui.py                                    # READ-ONLY, must stay passing
```

**Structure Decision**: Existing layout. No new source module. One new test file, following the
Feature-004 convention of a local fake service and `AppTest` with `build_service` patched.

## Complexity Tracking

None.
