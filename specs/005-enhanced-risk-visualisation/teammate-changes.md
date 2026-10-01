# Teammate Changes: Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Spec**: [spec.md](./spec.md) (Clarifications, decision 9) | **Plan**: [plan.md](./plan.md) | **Contract**: [contracts/dashboard-visual-contract.md](./contracts/dashboard-visual-contract.md)

Feature-005 changes two contributions that other team members wrote (TC-1, TC-3) and the
dashboard definition owned by Renny (the user) (TC-2). The team approved each change for US-28
(constitution Principle XVI). TC-2 is kept as a change log for revert purposes, not as a teammate
contribution. This record exists so that, if a
teammate is unhappy with a change, the product owner can revert that change quickly and on its
own. Every entry gives the original content and an exact revert route.

"Pending" values are filled in by Track E once the implementing commit exists. Paths are relative
to the repository root. Run revert commands from the repository root on the feature branch (or a
branch made from it), then run `uv run pytest -q` from `student_attrition_risk_app/`.

---

## TC-1 — Advisor page risk badge colours

| Field | Value |
|---|---|
| File + lines | `student_attrition_risk_app/src/student_attrition_risk/ui.py`, lines 144-145 (`.risk-badge`) and 155-156 (`.not-risk-badge`) |
| Original author + commit | GuaGuaGua88 (Lu), `8548e4f` "firstworkingBeforeValidation" (2026-09-17) |
| What changed | `.risk-badge` `background: #fee4e2;` → `#1565C0;`, `color: #b42318;` → `#FFFFFF;`. `.not-risk-badge` `background: #dcfae6;` → `#42A5F5;`, `color: #067647;` → `#172033;`. No other line of `ui.py`. |
| Why | US-28 decision 3: the badge uses the dashboard's category blues so both surfaces share one colour per category, with text contrast of at least 4.5:1 (spec FR-008). Wording and logic unchanged. |
| Commit that made it | `64d2b90` "Recolour the advisor risk badges to the dashboard blues (US-28)" (Track C; contains only `ui.py` and `tests/test_risk_badge_visualisation.py`) |
| Dependent files | `student_attrition_risk_app/tests/test_risk_badge_visualisation.py` (new, Track C) asserts the new colours and must be removed or reverted with this entry. |

**Revert**

- Preferred: `git revert 64d2b90` (the commit contains only `ui.py` and
  `tests/test_risk_badge_visualisation.py`).
- Or, only if `git diff 9469edc -- student_attrition_risk_app/src/student_attrition_risk/ui.py`
  shows no change other than these four lines:
  `git checkout 9469edc -- student_attrition_risk_app/src/student_attrition_risk/ui.py`.
  At `64d2b90` this holds: the four colour lines are the only `ui.py` change since `9469edc`.
- Otherwise, by hand, restore the exact original lines in `ui.py` (lines 144-145 and 155-156):

  ```css
  /* .risk-badge */
              background: #fee4e2;
              color: #b42318;
  /* .not-risk-badge */
              background: #dcfae6;
              color: #067647;
  ```

  New values being replaced: `.risk-badge` `background: #1565C0;` `color: #FFFFFF;`,
  `.not-risk-badge` `background: #42A5F5;` `color: #172033;`. Neither rule has a border.
- After the checkout or hand route (not needed after `git revert`), delete the new test file:
  `git rm student_attrition_risk_app/tests/test_risk_badge_visualisation.py`.
- Do **not** use `git checkout 8548e4f -- student_attrition_risk_app/src/student_attrition_risk/ui.py`:
  `ui.py` has later changes by other contributors (including Feature-004) that it would discard.

---

## TC-2 — Student Attrition Risk Overview dashboard definition

| Field | Value |
|---|---|
| File + lines | `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json` — line 15 (`risk_level` dimension), 302 / 314 (`counter_high` filter / title), 362 / 374 (`counter_low` filter / title), colour maps 459-468, 548-557, 731-740, 813-822, 895-904, chart frames, every layout `position.y` at or below the title, and the new `how_to_read` widget (line numbers as of `9469edc`) |
| Original author + commit | Committed by Renny (RennyMatis2000) in `9469edc` "Add dashboard file" (2026-09-30). Owner: Renny (the user), confirmed 2026-10-01. This entry is kept as a change log for revert purposes rather than as a teammate contribution. |
| What changed | Categories `High` / `Low` → `At Risk` / `Not At Risk` in the dimension, counter filters, counter titles and all five colour maps; At Risk listed first in each colour map; `"sort": {"by": "natural-order"}` on each chart's categorical axis; a description on every chart; new "How to read this dashboard" text widget at `y = 2` with all lower widgets moved down by 3. Full target state: contract §§ 1-6. |
| Why | US-28 decisions 2, 4 and 5: one vocabulary matching the advisor application, one documented order, and on-page explanations (spec FR-001–FR-014). |
| Commit that made it | `e4a253e` "Rename dashboard risk categories to At Risk / Not At Risk and add explanations" (branch `kickoff/005-dashboard`; dashboard JSON only, so `git revert e4a253e` also works if no later commit touches the file) |
| Dependent files | `student_attrition_risk_app/tests/test_dashboard.py` (TC-3) asserts the new labels; revert TC-3 together with TC-2. |

**Revert**

- Restore the original file (it has no other history since `9469edc`):
  `git checkout 9469edc -- "student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json"`.
- Then revert TC-3 as below, because its checks assert the new labels.
- If the dashboard was already published, re-publish the restored file (quickstart § 4) or the
  backup exported in quickstart § 4 step 3.

---

## TC-3 — Karen's dashboard tests

| Field | Value |
|---|---|
| File + lines | `student_attrition_risk_app/tests/test_dashboard.py` — lines 15-18 (new `json`, `re`, `pathlib.Path` imports), line 29 (`RISK_LEVEL_THRESHOLD` comment), 42-55 (`EXPECTED_WIDGET_TITLES`), 62-64 (`_risk_level`), 89-112 (`TestRiskLevelClassification`), 264-292 (live data-quality docstrings, column aliases and messages), and a new offline section (constants, helpers and `TestRepositoryDashboardDefinition`) appended after line 356 (line numbers as of the Track D commit) |
| Original author + commit | Karen (k224.lee / karen-lee1029), `0bff653` "Added test code for dashboard" and `049a3be` "Fixed test_dashboard.py code" (2026-09-24) |
| What changed | `High Risk` / `Low Risk` → `At Risk` / `Not At Risk` in `EXPECTED_WIDGET_TITLES`; `_risk_level` docstring and return values → `At Risk` / `Not At Risk`, and the four `TestRiskLevelClassification` assertions plus the mock-prediction check and its message follow; in the live `TestPredictionDataQuality` checks, docstrings, messages and SQL column aliases (`high_risk_cnt` → `at_risk_cnt`, `low_risk_cnt` → `not_at_risk_cnt`, `high` / `low` → `at_risk` / `not_at_risk`) use the new categories, with skip behaviour unchanged. New offline class `TestRepositoryDashboardDefinition` (25 test cases) reads the repository JSON relative to the test file and checks contract §§ 1-6: `risk_level` expression, no `High` / `Low` / `Medium` text anywhere, counter titles, filters and colours, every bar chart's colour map, natural-order sort, ascending `%` score buckets, chart descriptions, the `how_to_read` widget content and position, expected titles and no overlapping layout positions. Every original test name and the live `TestDashboardWidgets` class are unchanged. |
| Why | US-28 decision 6: the team approved updating this file so the dashboard checks describe the renamed categories and run offline in every suite run (spec FR-015). |
| Commit that made it | `e4fb15c` "Update dashboard tests for At Risk / Not At Risk and add offline contract checks" (`tests/test_dashboard.py` only) |
| Dependent files | Depends on TC-2. Reverting TC-3 alone while TC-2 stays would leave the old label replicas out of step with the dashboard. |

**Revert**

- Restore Karen's version exactly:
  `git checkout 439bc33 -- student_attrition_risk_app/tests/test_dashboard.py`
  (`439bc33` holds Karen's `049a3be` content unchanged; `git revert e4fb15c` also works if no
  later commit touches the file).
- Revert TC-2 at the same time (see above), or the restored tests will describe `High` / `Low`
  while the dashboard says `At Risk` / `Not At Risk`.
