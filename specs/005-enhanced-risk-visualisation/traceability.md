# Traceability Record: Feature-005 — Enhanced Student Risk Visualisation (US-28)

**Created**: 2026-10-01 | **Spec**: [spec.md](./spec.md) | **Contract**: [contracts/dashboard-visual-contract.md](./contracts/dashboard-visual-contract.md) | **Teammate changes**: [teammate-changes.md](./teammate-changes.md)

Maps every functional requirement (FR-001–FR-024) and success criterion (SC-001–SC-009) to the
task that delivered it and the automated check or manual evidence that verifies it (spec FR-023).

Verification names are in `student_attrition_risk_app/tests/` and are written as
`file::Class::test` or `file::test`. Parametrised tests are cited once by name. Tests marked
*(existing)* were already in the suite and are cited as evidence, not re-tested (no duplicated
coverage across features).

---

## 1. Functional requirements

### Risk categories and labels

| Requirement | Task(s) | Verified by |
|---|---|---|
| FR-001 Two categories, At Risk ≥ 50% / Not At Risk | T002 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_risk_level_dimension_uses_new_categories`; `test_dashboard.py::TestRiskLevelClassification::test_boundary_at_threshold`, `::test_just_below_threshold`, `::test_high_risk`, `::test_low_risk` (updated in T012) |
| FR-002 No High / Low / Medium anywhere | T002–T004 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_no_legacy_category_text` |
| FR-003 Counters titled and filtered by category; total unchanged | T003 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_counter_title_filter_and_colour`; `::test_all_expected_widget_titles_present` |
| FR-004 Filter and table column show the new values | T002 | Both read the `risk_level` dimension: `test_dashboard.py::TestRepositoryDashboardDefinition::test_risk_level_dimension_uses_new_categories`, `::test_no_legacy_category_text`; visual check in quickstart § 4 step 6 and § 5 shot 4 |
| FR-005 Badge wording and choice unchanged | T010 (no logic change) | `test_risk_badge_visualisation.py::test_badge_span_wraps_label_without_alert_widgets`; `test_ui.py` *(existing, unchanged)* |

### Colours

| Requirement | Task(s) | Verified by |
|---|---|---|
| FR-006 One colour map on all five charts | T004 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_chart_colour_map_matches_contract`, `::test_every_bar_chart_is_in_contract`; `test_risk_badge_visualisation.py::test_badge_backgrounds_match_dashboard_colour_maps` |
| FR-007 Counters use their category colour | — (already true, research R6) | `test_dashboard.py::TestRepositoryDashboardDefinition::test_counter_title_filter_and_colour` |
| FR-008 Badge blues with contrast ≥ 4.5:1 | T010 | `test_risk_badge_visualisation.py::test_badge_css_uses_dashboard_blues_and_contract_text_colours`, `::test_badge_text_contrast_is_at_least_4_5` |
| FR-009 Page-owned badge, no alert widgets | T010 | `test_risk_badge_visualisation.py::test_badge_span_wraps_label_without_alert_widgets` |
| FR-024 Score circle stays a white ring in the category colours, contrast ≥ 4.5:1 | Decision 10 (`46b4965`) | `test_risk_badge_visualisation.py::test_score_circle_uses_category_class`, `::test_score_circle_is_a_white_ring_in_dashboard_blues`, `::test_score_circle_text_contrast_is_at_least_4_5` |
| FR-025 Summary card edge in the category colour | Decision 11 (follow-up branch) | `test_summary_card_visualisation.py::test_summary_card_uses_category_class`, `::test_summary_card_edge_uses_dashboard_blues` |

### Ordering and explanations

| Requirement | Task(s) | Verified by |
|---|---|---|
| FR-010 Eight score ranges kept, ascending, `%` labels | T005 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_score_buckets_ascending_with_percent_labels`; boundaries by `test_dashboard.py::TestRiskScoreBucket` *(existing)* |
| FR-011 One documented category order | T004, T005 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_chart_colour_map_matches_contract` (At Risk first), `::test_chart_categorical_axis_natural_order`; visual check in quickstart § 4 step 6 |
| FR-012 "How to read this dashboard" panel | T007 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_how_to_read_widget_content`, `::test_how_to_read_position`, `::test_layout_has_no_overlapping_widgets` |
| FR-013 A description on every chart | T006 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_chart_description_shown` |
| FR-014 Explanations use the same names, threshold and colours | T006, T007 | `test_dashboard.py::TestRepositoryDashboardDefinition::test_how_to_read_widget_content`, `::test_chart_description_shown`, `::test_no_legacy_category_text` |

### Verification and scope

| Requirement | Task(s) | Verified by |
|---|---|---|
| FR-015 Dashboard tests describe the renamed categories | T012, T013 | `test_dashboard.py::TestRiskLevelClassification` (updated), `test_dashboard.py::TestRepositoryDashboardDefinition` (new, 25 cases) |
| FR-016 Badge checks in one new test file | T009 | `test_risk_badge_visualisation.py` (all tests) |
| FR-017 `test_ui.py` and other merged tests unchanged | T018 | § 3: `git diff 9469edc -- student_attrition_risk_app/tests/test_ui.py` is empty |
| FR-018 Every check runs offline | T013, T009 | § 3 suite run with no workspace or credentials; live classes skip as before |
| FR-019 Scoring, flag, threshold and ranges unchanged | — (met by absence of change) | § 3 diff: no file under `src/` other than `ui.py` styling, and no dataset query change beyond the `risk_level` literals |
| FR-020 Only the approved files change | T018 | § 3 `git diff 9469edc --stat` |
| FR-021 Quickstart publish steps | T017 | [quickstart.md](./quickstart.md) § 4; product owner runs it in T019 |
| FR-022 Every teammate change recorded with a revert route | T016 | [teammate-changes.md](./teammate-changes.md) TC-1–TC-5. The revert routes for TC-1 and TC-4 were dry-run in a throwaway worktree on 2026-10-01. |
| FR-023 Traceability record | T015 | This file |

## 2. Success criteria

| Criterion | Verified by |
|---|---|
| SC-001 All labels read At Risk / Not At Risk | FR-001, FR-002, FR-005 checks above; quickstart § 5 shots 1–5 |
| SC-002 5/5 charts and 2/2 counters share the colour per category | `test_dashboard.py::TestRepositoryDashboardDefinition::test_chart_colour_map_matches_contract`, `::test_counter_title_filter_and_colour` |
| SC-003 Score ranges ascending | `test_dashboard.py::TestRepositoryDashboardDefinition::test_score_buckets_ascending_with_percent_labels`; quickstart § 4 step 6 |
| SC-004 5/5 descriptions and 1 guide panel | `test_dashboard.py::TestRepositoryDashboardDefinition::test_chart_description_shown`, `::test_how_to_read_widget_content` |
| SC-005 Badge (and score ring) contrast ≥ 4.5:1 | `test_risk_badge_visualisation.py::test_badge_text_contrast_is_at_least_4_5`, `::test_score_circle_text_contrast_is_at_least_4_5` |
| SC-006 An advisor can name the At Risk colour and the threshold | Manual: the published "How to read this dashboard" panel (quickstart § 5 shot 1) |
| SC-007 0 failures, 0 new lint findings | § 3 |
| SC-008 No other merged test file changed | § 3 diff |
| SC-009 Published dashboard matches the repository | Manual, T019: quickstart §§ 4–5 screenshots, listed in § 4 below |

## 3. Final gate (T018), run on 2026-10-01 at merge commit `1f74a4f`

| Check | Result |
|---|---|
| `uv run pytest -q` | 296 passed, 13 skipped, 0 failed (baseline 260 passed, 13 skipped) |
| `uv run ruff check .` | 4 findings, all from before Feature-005 (`ui.py` I001 and two F401, `briefing_instructions.py` I001); none in Feature-005 lines |
| `git diff 9469edc -- student_attrition_risk_app/tests/test_ui.py` | empty |
| `git diff 9469edc --stat` (code files) | `dashboard/Student Attrition Risk Overview.lvdash.json`, `src/student_attrition_risk/ui.py`, `tests/test_dashboard.py`, `tests/test_risk_badge_visualisation.py` (new). Everything else is in `specs/005-enhanced-risk-visualisation/`. |

The 13 skips are the live `TestPredictionDataQuality` and `TestDashboardWidgets` checks, which
need a SQL warehouse or the workspace dashboard file, exactly as before Feature-005.

## 4. Published evidence (T019, product owner)

The product owner published the dashboard and captured these from the **published** view (quickstart §§ 4–5):

| Shot | Status | Date |
|---|---|---|
| 1. Title, guide panel and counters | Captured and checked: guide panel under the title; At Risk 391,388 + Not At Risk 582,382 = Total 973,770 | 2026-10-01 |
| 2. Risk Analysis row | Captured and checked: At Risk first in every legend; score ranges ascending (46-48% → 52-54%; 0-46% and 54-100% hold no students, so no bar is drawn) | 2026-10-01 |
| 3. Demographic Breakdown row | Captured and checked: one colour per category, descriptions shown | 2026-10-01 |
| 4. Filter by Risk Level open | Captured and checked: options All / At Risk / Not At Risk | 2026-10-01 |
| 5. Advisor page, at-risk and not-at-risk students | Pending: first capture showed the deployed app still running pre-merge code (red/green). Retake after redeploying from `main` with this follow-up merged. | — |

Observation: the stacked demographic charts draw the Not At Risk segment first (left); the legends
list At Risk first, as the contract requires.
