---
description: "Task list for Feature-005 — Enhanced Student Risk Visualisation (US-28)"
---

# Tasks: Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Input**: Design documents from `specs/005-enhanced-risk-visualisation/`
**Prerequisites**: [plan.md](./plan.md) (change map), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/dashboard-visual-contract.md](./contracts/dashboard-visual-contract.md), [quickstart.md](./quickstart.md), [teammate-changes.md](./teammate-changes.md)

**Tests**: Required. Spec FR-015 and FR-016 require offline dashboard checks in the approved
`tests/test_dashboard.py` and badge checks in the new `tests/test_risk_badge_visualisation.py`.
`tests/test_ui.py` and every other merged test file stay unchanged (FR-017).

**Organisation**: One phase per implementation track so tracks can be handed to separate agents.
Story labels map to spec.md: **US1** = consistent categories and colours (P1), **US2** = ordered and
explained charts (P2), **US3** = badge matches dashboard (P3), **US4** = publish, evidence and
revert (P4). Track B delivers US1 + US2 in the dashboard, Track C delivers US3, Track D verifies
US1 + US2, Track E delivers US4.

All paths below are relative to `student_attrition_risk_app/` unless they start with `specs/`.
JSON line numbers are as of `9469edc` (plan.md § Change map). Only the listed files and lines may
change. Never edit `tests/test_ui.py` or any other merged test file except `tests/test_dashboard.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)

## Files touched (per plan.md § Project Structure)

| Action | Path | Track |
|---|---|---|
| EDIT | `dashboard/Student Attrition Risk Overview.lvdash.json` | B |
| EDIT (badge lines 144-145, 155-156; score circle lines 181, 187, 193-196, 660-664, 702 — decision 10) | `src/student_attrition_risk/ui.py` | C |
| NEW | `tests/test_risk_badge_visualisation.py` | C |
| EDIT (approved) | `tests/test_dashboard.py` | D |
| NEW | `specs/005-enhanced-risk-visualisation/traceability.md` | E |
| EDIT | `specs/005-enhanced-risk-visualisation/teammate-changes.md`, `quickstart.md` | E |
| READ-ONLY | `tests/test_ui.py`, every other file in `tests/`, every other file in `src/` | — |

---

## Phase 1: Setup

- [x] T001 From `student_attrition_risk_app/`, run `uv sync --dev`, `uv run ruff check .` and `uv run pytest -q`; record the baseline counts in the task notes. Baseline at branch creation: 260 passed, 13 skipped, 0 failed; ruff reports 4 pre-existing findings (`ui.py` I001 and two F401, `briefing_instructions.py` I001) in lines Feature-005 does not own — they are not fixed here (Principles II, XVI).

**Checkpoint**: Baseline green. No foundational phase: Tracks B and C share no prerequisite beyond T001.

---

## Phase 2: Track B — dashboard categories, colours, order and explanations (US1 P1 🎯 MVP, US2 P2)

**Goal**: The repository dashboard definition matches contract §§ 1-6 (spec FR-001–FR-004, FR-006, FR-007, FR-010–FR-014).

**Independent test**: `python -m json.tool` accepts the file; a search for `'High'`, `'Low'`, `"High"`, `"Low"`, `High Risk`, `Low Risk` or `Medium` as a category value finds nothing; Track D's checks pass once written.

- [x] T002 [US1] In `dashboard/Student Attrition Risk Overview.lvdash.json` line 15, change the `risk_level` dimension `expr` to `"CASE\n  WHEN source.attrition_risk_percentage >= 50 THEN 'At Risk'\n  ELSE 'Not At Risk'\nEND"` (contract § 1). Do not rename the dimension or touch `risk_score_bucket`.
- [x] T003 [US1] In the same file, `counter_high`: filter (line 302) `IN ('High')` → `IN ('At Risk')`, title (line 314) `High Risk` → `At Risk`; `counter_low`: filter (line 362) `IN ('Low')` → `IN ('Not At Risk')`, title (line 374) `Low Risk` → `Not At Risk`. Keep widget names and `fontColor`s.
- [x] T004 [US1] In the same file, replace the colour-map `mappings` of `chart_risk_donut`, `chart_risk_by_faculty`, `chart_risk_study_mode`, `chart_risk_gender` and `chart_risk_intl` (lines 459-468, 548-557, 731-740, 813-822, 895-904) with exactly `[{"color": "#1565C0", "value": "At Risk"}, {"color": "#42A5F5", "value": "Not At Risk"}]` in that order (contract § 2).
- [x] T005 [US2] In the same file, add `"sort": {"by": "natural-order"}` inside the categorical `scale` of each of the five charts — `y` for `chart_risk_donut`, `chart_risk_study_mode`, `chart_risk_gender`, `chart_risk_intl`; `x` for `chart_risk_by_faculty` (contract § 3, research R2). Do not change the eight bucket labels.
- [x] T006 [US2] In the same file, set `showDescription: true` and `description: {"value": <text>, "fields": []}` on the `frame` of all five charts, using the exact text in contract § 4 (rewords the two existing descriptions, adds three). Leave the table, counters and filters as they are.
- [x] T007 [US2] In the same file, add 3 to `position.y` of every layout item with `y >= 2`, then insert the `how_to_read` layout item exactly as in contract § 5 at `{x: 0, y: 2, width: 12, height: 3}`. Preserve the file's existing indentation style and key order elsewhere.
- [x] T008 [US1] Track B gate: validate the JSON (`uv run python -m json.tool "dashboard/Student Attrition Risk Overview.lvdash.json" > /dev/null`); confirm with a short throwaway script (not committed) that no two layout items overlap and that 19 layout items exist; `uv run pytest -q` still shows 0 failed (Karen's replicas do not read the JSON yet). Commit Track B's file on its own.

**Checkpoint**: Dashboard definition complete. Unblocks Track D.

---

## Phase 3: Track C — advisor page badge matches the dashboard (US3, P3) — parallel with Track B

**Goal**: Badge colours match the dashboard and keep text contrast of at least 4.5:1 (spec FR-005, FR-008, FR-009, FR-016).

**Independent test**: `uv run pytest tests/test_risk_badge_visualisation.py tests/test_ui.py -q` passes.

- [x] T009 [P] [US3] Create `tests/test_risk_badge_visualisation.py` (research R5): module docstring naming Feature-005 / US-28 and `specs/005-enhanced-risk-visualisation/contracts/dashboard-visual-contract.md` § 7; a local minimal fake service on `MockStudentRepository` patched through `student_attrition_risk.main.build_service` with `st.cache_resource.clear()` and `AppTest.from_file(<ui.py>, default_timeout=10)` (same pattern as `tests/test_defect_resolution.py`, which is not imported or edited); tests: (1) parametrised over `synthetic-student-001` → `risk-badge` / `At Risk` and `synthetic-student-002` → `not-risk-badge` / `Not At Risk`: the summary markdown contains `<span class="<class>">` wrapping the label, and `at.info`, `at.success`, `at.warning` are empty; (2) parse the `.risk-badge` and `.not-risk-badge` rules from the rendered `<style>` markdown and assert `background` `#1565C0` / `#42A5F5` and `color` `#FFFFFF` / `#172033` (case-insensitive); (3) compute the WCAG contrast ratio of each parsed pair and assert ≥ 4.5. Confirm (2) and (3) fail before T010.
- [x] T010 [US3] In `src/student_attrition_risk/ui.py`, change only lines 144-145 (`.risk-badge`: `background: #1565C0;`, `color: #FFFFFF;`) and 155-156 (`.not-risk-badge`: `background: #42A5F5;`, `color: #172033;`) (contract § 7). No other line, no label or logic change, no Streamlit alert widget.
- [x] T011 [US3] Track C gate: `uv run ruff check tests/test_risk_badge_visualisation.py` clean and `uv run ruff check src/student_attrition_risk/ui.py` shows only the 3 baseline findings (do not fix them); `uv run pytest -q` shows 0 failed; `git diff --stat` lists only the two Track C files. Commit Track C's two files on their own (so TC-1 can be reverted with one `git revert`).
- [x] T011a [US3] (Decision 10, added 2026-10-01) In `src/student_attrition_risk/ui.py`, recolour the relative-risk score ring per contract § 7a (FR-024): `.risk-circle` border and text `#1565C0` on the unchanged white fill; new `.risk-circle.not-risk-circle` rule (`#42A5F5` ring, `#172033` text); `circle_class` chosen from `attrition_risk_flag` and used on the score `<div>`. Add the three score-circle tests to `tests/test_risk_badge_visualisation.py`. Committed on its own as `46b4965` (TC-4).

---

## Phase 4: Track D — dashboard checks describe and verify the new visual language (US1, US2) — after Track B

**Goal**: Karen's approved dashboard test file uses the new labels and checks the repository definition offline (spec FR-015, FR-018).

**Independent test**: `uv run pytest tests/test_dashboard.py -v` — all offline tests pass; live classes skip as before.

- [x] T012 [US1] In `tests/test_dashboard.py`: line 26 comment → `-> 'At Risk'`; lines 39-52 `EXPECTED_WIDGET_TITLES` replace `"High Risk"`, `"Low Risk"` with `"At Risk"`, `"Not At Risk"`; lines 59-61 `_risk_level` docstring and return values → `'At Risk'` / `'Not At Risk'`; lines 86-108 `TestRiskLevelClassification` expected values and message wording follow; lines 262-279 live-check docstrings and messages say "At Risk" / "Not At Risk". Keep every test function name and the live `TestDashboardWidgets` class unchanged.
- [x] T013 [US1] [US2] Append `class TestRepositoryDashboardDefinition` after line 353 of `tests/test_dashboard.py` (research R4): load `Path(__file__).resolve().parent.parent / "dashboard" / "Student Attrition Risk Overview.lvdash.json"`; locate widgets by name; one test per rule — (a) `risk_level` expr contains `>= 50`, `'At Risk'`, `'Not At Risk'`; (b) no `'High'` / `'Low'` / `'Medium'` category literal in any dimension expr, filter expression or mapping value; (c) counter titles and filter expressions per contract § 1, and counter `fontColor`s per contract § 2 (`counter_high` `#1565C0`, `counter_low` `#42A5F5`); (d) each of the five charts' mappings equals contract § 2 in order; (e) each chart's categorical axis has `sort.by == "natural-order"`; (f) the bucket labels from the dimension expr, sorted as text, equal `[b[2] for b in RISK_SCORE_BUCKETS]`; (g) every chart has `showDescription` true and a non-empty description; (h) `how_to_read` text contains `How to read this dashboard`, `At Risk`, `Not At Risk`, `50%`, `#1565C0`, `#42A5F5`; (i) every `EXPECTED_WIDGET_TITLES` entry is present (title read from `title.value` or a plain-string `title`); (j) no two layout items overlap. Use parametrize where it removes repetition; no new fixtures module.
- [x] T014 [US1] Track D gate: `uv run ruff check tests/test_dashboard.py` clean; `uv run pytest -q` shows 0 failed. Commit `tests/test_dashboard.py` on its own.

**Checkpoint**: US1 and US2 verified offline.

---

## Phase 5: Track E — traceability, publish steps, converge (US4, P4) — after Tracks B, C, D

**Goal**: Every requirement is traceable, every teammate change is revert-ready, and the product owner can publish (spec FR-021–FR-023).

- [x] T015 [US4] Create `specs/005-enhanced-risk-visualisation/traceability.md` in the style of `specs/003-briefing-workflow-testing/traceability.md`: one row per FR-001–FR-023 and SC-001–SC-009 → task(s) → verifying test (file::name) or manual evidence step (quickstart §§ 4-5); a section listing scope requirements met by absence of change (FR-017, FR-019, FR-020) with the `git diff 9469edc --stat` evidence.
- [x] T016 [US4] In `specs/005-enhanced-risk-visualisation/teammate-changes.md`, replace each "pending" with the Track B, C and D commit hashes; confirm each TC entry's line numbers and revert command against the final diff.
- [x] T017 [US4] Run the `speckit-converge` assessment: compare the final JSON, `ui.py` and tests with spec, plan and contract; confirm quickstart § 4 (publish) and § 5 (evidence) match the final dashboard (19 widgets, `how_to_read` under the title); append any remaining unbuilt work as new tasks.
- [x] T018 Final gate: `uv run ruff check .` shows only the 4 baseline findings (T001); `uv run pytest -q` 0 failed; `git diff 9469edc --stat` shows only the files in "Files touched" plus this feature's `specs/005-enhanced-risk-visualisation/` documents; `git diff 9469edc -- student_attrition_risk_app/tests/test_ui.py` is empty. Record counts in `traceability.md`.
- [x] T019 [US4] **Product owner (manual, not an agent)**: follow quickstart § 4 to replace and publish the dashboard in the workspace, and § 5 to capture light, professional screenshots; list them in `traceability.md`.
- [x] T020 [US1] (Decision 12, added 2026-10-01) In `dashboard/Student Attrition Risk Overview.lvdash.json` line 25, change the `student_id` dimension to `LEFT(source.student_deidentified_hash, 16)` (contract § 8, FR-026); update the `_student_id` replica and `TestStudentIdTruncation` in `tests/test_dashboard.py` and add an offline check and a live uniqueness check. Gate: `uv run pytest -q` 0 failed.
- [x] T022 [US3] (Decision 13, added 2026-10-01) Let the advisor page retrieve a student by the dashboard's 16-character Student ID (FR-027, contract § 9): `find_predictions_by_student_id` in both repositories and the `StudentRepository` port, Student ID fallback in `StudentService.get_student_profile`, "Student ID" wording in `ui.py` (TC-6) and `tests/test_ui.py` (TC-7), new `tests/test_student_id_lookup.py`. Gate: `uv run pytest -q` 0 failed.
- [ ] T021 [US4] **Product owner (manual)**: re-publish the dashboard in place (quickstart § 4) so the table and Search Student show 16-character Student IDs; redeploy the advisor app from `main`; copy one Student ID from the dashboard into the app and check it retrieves that student.

---

## Dependencies & execution order

```text
T001 ──┬── Track B (T002→T003→T004→T005→T006→T007→T008) ──┐
       │                                                   ├── Track D (T012→T013→T014) ──┐
       └── Track C (T009→T010→T011) ───────────────────────┼──────────────────────────────┴── Track E (T015→T016→T017→T018) → T019 (PO)
```

- **B and C are independent** (disjoint files) and run in parallel after T001.
- **D depends on B**: its offline checks assert the JSON that B produces.
- **E depends on B, C and D**: it records their commits and runs the final gate.
- Within Track B, T002–T007 edit one file and run in sequence.

## Parallel opportunities

- After T001: Track B and Track C on separate agents.
- Within Track C: T009 (new test file) can be written while Track B runs.

## Implementation strategy

1. **MVP = Track B T002–T004** (US1): one vocabulary and one colour map — the core of US-28's "consistent risk categories ... and labels".
2. Complete Track B (US2 ordering and explanations) and Track C (US3 badge) in parallel.
3. Track D locks both in with offline checks.
4. Track E records traceability and revert routes; the product owner publishes and captures evidence. No push or merge without the product owner's explicit approval.
