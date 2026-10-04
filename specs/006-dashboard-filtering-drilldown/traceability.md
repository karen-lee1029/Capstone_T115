# Traceability: Feature-006 (US-29)

Criterion → stories: "applies available filters" → US1; "selects a relevant dashboard view" → US2
(and the US-27 pages); "updates consistently" → US1 scenarios 2–4, SC-002; "examine ... in greater
detail" → US3. Planned test names in `tests/test_dashboard_filtering.py` (TDF) are confirmed at
implementation. Matrix rows (A0 – D4) are in `quickstart.md`; a row not run is reported pending, never passed.

| FR | Verified by |
|---|---|
| FR-001 | TDF `test_single_global_filters_page`, `test_page_order` |
| FR-002 | TDF `test_global_filters_match_contract` |
| FR-003 | TDF `test_filter_fields_resolve_to_dataset_dimensions` |
| FR-004 | TDF `test_no_filter_on_sensitive_attributes` (a); TDF `test_sensitive_charts_are_isolated`, `test_gender_chart_is_on_gender_breakdown` (b); matrix A0, B4, B7 (Demographic table, Q21 → Q22) |
| FR-005 | TDF `test_no_fixed_filter_conflicts_with_global_filters`; matrix A1 – A11 |
| FR-006 | TDF `test_student_list_risk_filter_replaced` |
| FR-007 | TDF `test_filters_apply_immediately` |
| FR-008 | TDF `test_page_widgets_share_relationship_graph`; matrix B1 – B3, B5, B6 |
| FR-009 | TDF `test_filters_apply_immediately`; matrix B1, B4 |
| FR-010 | TDF `test_each_analysis_page_has_one_drill_table` |
| FR-011 | TDF `test_drill_table_columns_match_contract` |
| FR-012 | TDF `test_drill_table_sorted_by_risk_desc_with_boundary_text`; matrix C1, C3, C4 |
| FR-013 | TDF `test_drill_table_uses_student_id_dimension`, `test_preserved_parts_match_base` |
| FR-014, FR-015 | TDF `test_how_to_filter_panel_content`; matrix D3, D4 |
| FR-016 | TDF `test_preserved_parts_match_base`; `git diff --stat` shows no `src/` change |
| FR-017 | `test_dashboard.py` `test_layout_has_no_overlapping_widgets` (per page after FR-020; not duplicated in TDF) |
| FR-018 | `test_dashboard.py` `test_chart_colour_map_matches_contract[*]`, `test_chart_categorical_axis_natural_order[*]`, `test_chart_description_shown[*]`, `test_every_bar_chart_is_in_contract` (7 charts) |
| FR-019 | `test_dashboard.py` `test_all_expected_widget_titles_present` |
| FR-020 | `test_dashboard.py` `test_layout_has_no_overlapping_widgets` |
| FR-020a | `test_dashboard.py` `test_student_id_is_labelled_de_identified` |
| FR-021 | `test_ui.py` `test_at_risk_student_shows_profile_with_briefing_actions`, `test_generate_briefing_displays_text_metadata_and_download`, `test_retrieve_saved_and_review_checkbox_are_not_rendered` |
| FR-022 | Code review of the two repaired files against plan D-8 / D-9 |
| FR-023 | Code review: one new US-29 test file |
| FR-024 | Full `pytest` and `ruff` output in the implementation handoff |
| FR-025 | `quickstart.md` workspace acceptance matrix (rows A0 – D4) |
| FR-026 | `teammate-changes.md` |
| FR-027 | This file |
