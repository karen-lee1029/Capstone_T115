# Implementation Handoff: Feature-006 — Interactive Dashboard Filtering and Drill-Down (US-29)

**For**: Codex Code Reviewer · **From**: Claude Coder · **Date**: 2026-10-04
**Branch**: `agent/claude-coder-mutdg3d2` (local commits only; base `origin/main` `0409d7e`)
**Design**: this folder — `spec.md` (Q1 – Q22), `plan.md`, `contracts/dashboard-interaction-contract.md`
**Commits**: `f745a62` implementation · `bb83760` CODE-02 / CODE-03 · Stage 5 commit (CODE-01, Q21 → Q22)

## What changed

| File | Change |
|---|---|
| `student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json` | **Filters** page (`PAGE_TYPE_GLOBAL_FILTERS`) with 8 multi-select filters. New **Gender Breakdown** page holding Risk by Gender (Q16 = a), with Risk by Origin widened and the Demographic subtitle updated. Student List page-level risk filter `310fbbb0` removed and Search Student widened. Three "Students in this view" tables, sorted `risk_pct` DESC through `orders`, with no row cap and the 100,000-row description (Q17 = a). "How to filter and drill down" panel on Overview. Notes and footers moved down. Datasets, relationship graph, `uiSettings` and every other widget are unchanged (checked against base). |
| `student_attrition_risk_app/tests/test_dashboard_filtering.py` (new) | 40 offline checks for FR-001 – FR-016 (one file, Q11); 32 at `f745a62`, +8 binding cases in `bb83760` |
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

### Code review (Codex, of `f745a62`)

| Finding | Disposition | Where |
|---|---|---|
| CODE-01 (P2) tables exempted from the Q6 check | **Accepted.** The official docs list Table as a cross-filter source; research R-8 corrected. Q21 = a (test "Ignored filters", then suppress) could not be carried out: the option is not offered in this workspace's editor, the dashboard authoring assistant could not set it, and its JSON format is unknown (an API key test proves nothing, since unknown spec keys are kept). Q22 = a → fallback to **Q21 b, observe first**. The dashboard is unchanged and Karen's charts are not touched. The blanket table exemption is replaced by `OBSERVED_SENSITIVE_TABLES = {"drill_table_demographic"}`, so any other table showing a sensitive field beside other widgets fails. Workspace row **B7** must show no narrowing; if it narrows, Q6 is broken and it returns to the product owner. | spec Q21 / Q22 / FR-004, contract C-1, research R-8, quickstart B7, traceability, review-dispositions, `test_sensitive_charts_are_isolated` |
| CODE-02 (P2) checks validated aliases, not bindings | **Accepted and fixed** (`bb83760`). `test_filter_binding_is_complete` (8 cases) and expression checks on every table column. All 3 reviewer faults now fail a test. | `tests/test_dashboard_filtering.py` |
| CODE-03 (P3) acceptance text said four pages | **Accepted and fixed** (`bb83760`). SC-001 and matrix A1 – A2 name all 5 canvas pages. | spec SC-001, quickstart |
| Stale R-2 wording | **Accepted and fixed** (`bb83760`). R-2 says "not yet verified" and points to A1 – A11. | research R-2 |

## R-3 format evidence

The agent created a scratch workspace dashboard, "US29 format probe" (`01f1bfdf60b11b2188494e9fab7b0937`,
not published), through `databricks lakeview create` at the product owner's request. The server kept
the global-filter page, the filter widget and query `orders`, and dropped an unknown control key
(research R-3). For Q21 one further approved API update added candidate ignore keys to the probe,
and the product owner changed one probe chart's type while looking for the option. **The product owner
decided to keep the probe (2026-10-05).** It is not part of the deliverable and is not to be deleted.

## Verification (2026-10-04, from `student_attrition_risk_app/`, final Stage 5 run)

| Command | Base `0409d7e` | Now |
|---|---|---|
| `uv run pytest -q` | 24 failed, 285 passed, 14 skipped | **0 failed, 352 passed, 14 skipped** |
| `uv run pytest tests/test_dashboard_filtering.py -q` | — | 40 passed, 0 skipped (preservation checks ran against `0409d7e`) |
| `uv run ruff check .` | 1 finding (I001 `briefing_instructions.py:9`) | Same single base finding; no new finding |

Count reconciliation: 285 + 24 = 309; test_ui −4 + 1 = −3; 7 charts instead of 5 in three
parametrised Feature-005 checks = +6; new file +40 → 352.

**Mutation check** (7 faults injected one at a time into the dashboard JSON; file restored byte for
byte, confirmed): every fault fails at least one test.

| Fault | Result |
|---|---|
| Gender chart put back on Demographic Breakdown | 2 failed |
| Overview table `orders` removed | 1 failed |
| Faculty filter alias renamed to `gender` | 3 failed |
| Reviewer 1: Faculty filter expression → `gender` | 3 failed |
| Reviewer 2: Faculty filter encoding emptied | 1 failed |
| Reviewer 3: Overview Risk % expression → constant 0 | 1 failed |
| Q22: Gender column added to the Course Analysis table | 2 failed |

## Pending (workspace only — not claimed)

- Publishing is the product owner's job (quickstart). Every workspace acceptance matrix row (A0 – D4)
  is **pending**: filter propagation to every widget (R-2), cross-filtering, Gender isolation (B4), the
  100,000 boundary and sort-before-truncation (C4), the missing-enrolment case (D3), and **B7**: a
  click in the Demographic Breakdown table must not narrow Risk by Age Band or Risk by Origin
  (Q21 → Q22, observe first). FR-004 for that table is unproven until B7 runs.
- If any row fails, implementation stops and escalates via god (plan D-2). No query change is made
  without an SDD amendment.

## Workspace acceptance round 2 (product owner, published `a5245c1`)

Results are taken from the product owner's own report ("Human overview and testing of pending findings
before committing to origin.pdf"). Its A3 – A7 numbering is shifted from the quickstart's. "Pass" and
"Fail" are the product owner's words.

| Row | Result | Note |
|---|---|---|
| A0 | Pass | |
| A1 | Pass | At Risk counter blank (the platform shows zero as blank) |
| A2 (Faculty) | Fail | Only "null" offered |
| A3 (Course Level), A5 (Origin), A6 (Age Band), A8 (Commencing/Continuing) | Fail | UNRESOLVED_COLUMN on every chart |
| A4 (Field of Education) | Not reported | Bound the same way as the failing filters |
| A7 (Study Mode) | Fail | Only "null" offered |
| A9 | Pass for Risk Level only | |
| A10 | Fail | Faculty null, Course Level error |
| A11 | Pass | |
| B1 | Pass | |
| B2 | Fail | Faculty only All / null |
| B3 | Pass | |
| B4 | Pass | Nothing narrows |
| B5, B6 | Fail | Bars highlight but do not narrow |
| B7 | Pass, except the second half | Gender click narrows nothing; Age Band and Origin clicks do not narrow the table |
| C1, C2 | Pass | |
| C3, C4 (outside-table search) | Blocked | No filter can narrow below 100,000. The sort order works (C4) |
| D1 | Fail | Faculty |
| D2 | Fail | No match or null raises an error |
| D3 | Blocked | Enrolment filter error |
| D4 | Pass | |

**Diagnosis** (read-only workspace check, 2026-10-05). The published dashboard matched `a5245c1`
exactly.
1. Faculty and Study Mode are NULL in every source row (study-area table: 1,100 rows; enrolment
   rows: 973,770).
2. The enrolment-bound filters' conditions reach queries that hold only prediction columns. The
   relationship filter propagation the design relied on (R-2) is Databricks Public Preview (3 and
   10 Sep 2026).
3. Chart clicks highlighting without narrowing are inferred to be the same propagation limit.

**Decisions**:
- Q23 = a: a workspace admin checks the two previews, then the A and B rows are re-run.
- Q24 = a, with the product owner's rule that a filter showing only null, or erroring, is removed.

**Changed in this round**:
- Faculty and Study Mode filters removed; the 6 remaining filters stack without gaps.
- Help panel text updated.
- New checks: `test_no_filter_on_empty_source_fields` and `test_filters_stack_without_gaps`.
- Spec Q23 / Q24 and FR-002, contract C-1, research, data model, quickstart rows (A2, A3, A7, A9,
  A10, B2, B3, D1 re-pointed) and review-dispositions.

**Verification**:
- `uv run pytest -q`: 350 passed, 14 skipped, 0 failed. The −4 is the two parametrised filter checks
  losing two cases each; +2 new checks.
- US-29 file: 38 passed.
- Ruff: base I001 only.
- Mutation: 8 of 8 faults caught. Faults 3 – 5 now target the Course Level filter; new fault: "Faculty
  filter put back" (2 failed).

**Still pending**:
- The preview check (admin), then a re-run of A2 – A10, B2, B5 – B7, C3, C4, D1 – D3.
- Under the product owner's rule, any enrolment filter still erroring after that check is removed.
  If all five go, only Risk Level remains, which would hollow out US-29's filtering. That outcome
  goes back to the product owner, not straight to removal.

## Round 3: Q23 outcome and Q25 (2026-10-05)

**Q23 = a outcome**: no Previews page in this workspace. The product owner checked the user menu,
Settings and the direct URL, and confirmed it is Databricks Free Edition. The account is a workspace
admin (read-only check), so the gap is not a permissions problem.

**Q25 = a**: the five enrolment filter fields are joined into Karen's prediction dataset, and all six
filters bind to it.
- A read-only run of the joined query returned 973,770 rows and 973,770 distinct students. Every
  filter field is filled. Course Level has 4 values: Undergraduate 607,339, Postgraduate (Coursework)
  243,454, Other 85,137, HDR 37,840.
- The course table has a unique key, 1,544 of 1,544.
- Widget queries, dimensions and measures are unchanged. This is a C-5 exception for the dataset
  source only, logged as teammate change TC-4. Karen's `test_prediction_dataset_source_table` now
  asserts the source reads from the prediction table.
- Evidence that this binding reaches the charts: the Risk Level filter is already bound to this
  dataset, and it narrowed every widget (B1 passed).

**New checks**: `test_prediction_source_joins_only_filter_fields`. It requires one row per student,
the LEFT JOIN, exactly the five `enrol_*` columns and no sensitive column. Preservation now allows
only the prediction source to change.

**Verification**:
- `uv run pytest -q`: 351 passed, 14 skipped, 0 failed.
- US-29 file: 39 passed.
- Ruff: base I001 only.
- Mutation: 10 of 10 faults caught. New faults: "Age Band filter bound to the enrolment dataset
  again" (2 failed) and "gender column joined into the prediction source" (1 failed).

**Pending (product owner)**: re-publish from this commit, then re-run A2 – A10, B2, B5 – B7, C3, C4
and D1 – D3. Chart clicks that only highlight (B5, B6, the second half of B7) may persist, because Q25
does not change how charts query. If they do, that comes back as a decision.

## Round 3 results (product owner, published `34597ff`)

Source: the product owner's "Notes on changes and recompleting failed tests for Feature.pdf".

| Row | Result | Note |
|---|---|---|
| A2 (Course Level) | Pass | "All filters work properly". Double filtering shown (Course Level + Field of Education) |
| A4, A5, A6, A8, A9, A10 | Pass | |
| B1 / B2 | Fail | Clicking At Risk or Not At Risk on Risk by Course Level: Risk by Field of Education and the table error with "INVALID_PARAMETER_VALUE: Filter expression references multiple sources: student_attrition_risk_prediction, Student_Enrolment_Details". This happens on every page. B1 passed in round 2 at `a5245c1` |
| B5 | Fail | The same error after an Age Band or Origin click |
| B6 | Pass | Risk Score Range click narrows the counters, the chart and the table |
| B7 | Fail (error, not narrowing) | A Gender cell click makes Risk by Age Band and Risk by Origin error. Nothing narrows by gender, but the charts stop rendering |
| C3 | Pass | |
| C4 | Not run as written | Searched an Undergraduate ID while filtered to HDR and got "no data". That is correct filtering, not the C4 case. The agent's instruction was ambiguous |
| D1, D2 | Pass | D2 shows "No data" rather than 0, which the product owner accepts |
| D3 | Not applicable | Every student has an enrolment record. Per the product owner, the missing-enrolment sentence is removed from the help panel (this commit) |

The probe dashboard stays by the product owner's decision. Its deletion is no longer pending.

## Round 4: Q26 (2026-10-05)

**Q26 = a**: the five charts `028257ed`, `90548010`, `eaf7eaf4`, `292bc630` and `52cb0fd3`, plus the
Course and Demographic drill tables, now take their enrolment fields from the joined prediction
columns. Selections on analysis pages therefore use one dataset. The joined source gains
`enrol_gender`, for display only; no filter binds to it. A read-only run returned 973,770 rows, one per
student, with gender filled for all. This is a C-5 exception for Karen's chart queries (TC-5); her
tests needed no change.

**Age bands**: the product owner reports they now work. The data has 11 bands (read-only check).

**C4**: still failing as reported. With no filters, searching `64e9c59460e17c3a` (Risk % 49.7;
613,371 students rank above it, so it is outside the top 100,000) shows "No Data". Cause not yet
known; see the question to the product owner on which search box was used.

**New checks**: `test_selections_use_one_dataset`. Preservation compares the five charts with base
after the field rename.

**Verification**:
- `uv run pytest -q`: 352 passed, 14 skipped, 0 failed.
- Ruff: base I001 only.
- Mutation: 11 of 11 faults caught. New fault: "Age Band chart bound to the enrolment dataset again"
  (2 failed).

**Pending (product owner)**: re-publish, then run the quickstart round 4 re-test (B1 – B3, B5, B7,
C4).

## Round 4 results (product owner, published `f531edf`)

| Row | Result | Note |
|---|---|---|
| B1, B2, B3 | Pass | No "multiple sources" error. Course Analysis selections narrow, combine with filters and clear independently |
| B5 | Pass | Age Band and Origin bar clicks narrow the other chart and the table without error (product owner confirmed; the first note labelled B7 as B5) |
| B7 | Pending product owner decision (Q27) | A click in the Demographic table selects that student's row, so Risk by Age Band and Risk by Origin narrow to one student. That is narrowing by student, not by gender. The written expectation ("do not change") is not met; the intent of Q6 ("never narrow by gender") appears to be met |
| C4 | Pass | With no filters, Search Student on Student List finds `64e9c59460e17c3a` (ranked below the top 100,000). The magnifier inside a "Students in this view" table only searches the up-to-100,000 rows it holds, as its description states |
