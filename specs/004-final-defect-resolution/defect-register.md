# Defect Register: Feature-004 — Final Defect Resolution (US-20)

**Created**: 2026-09-24 | **Spec**: [spec.md](./spec.md) | **Backlog**: US-20 (GitHub issue #27)

Consolidated from the US-20 defect sweep (tracks A–D) run on `feat/feature-004-final-defect-resolution`
at `3181882` (main at `cdaf89e`). All source paths are under
`student_attrition_risk_app/src/student_attrition_risk/` unless they start with `tests/`
(`student_attrition_risk_app/tests/`). Line numbers are as of `3181882`.

Every entry starts with status **Open**. A Feature-004 fix moves to **Closed** only when its
regression test group (named after the register ID) passes in
`tests/test_defect_resolution.py`.

## 1. Baseline (before any Feature-004 change)

| Check | Result |
|---|---|
| `uv run pytest -q` | 209 passed, 5 failed, 13 skipped |
| Failures | All 5 in `tests/test_ui.py` (register A1–A4 / C1) |
| Skips | 13 in `tests/test_dashboard.py` (need a live Databricks workspace) |
| `uv run ruff check .` | 7 errors: 5 × I001 (import order), 2 × F401 (unused import); all autofixable (A8, A9, A10) |

### 1.1 Post-fix results (after B2, C3, B4, B1 merged; `27c5db0`, 2026-09-24)

Quickstart §§ 1-2 (T019), run from `student_attrition_risk_app/`.

| Check | Before (`3181882`) | After (`27c5db0`) |
|---|---|---|
| `uv run pytest -q` | 209 passed, 5 failed, 13 skipped | **236 passed, 5 failed, 13 skipped** |
| Failures | 5, all `tests/test_ui.py` (A1–A4 / C1) | The same 5 `tests/test_ui.py` tests, no others |
| Skips | 13 in `tests/test_dashboard.py` | Unchanged |
| `uv run pytest tests/test_defect_resolution.py -q` | — (file did not exist) | 27 passed (B2 6, B4 4, C3 9, B1 8) |
| `uv run ruff check` on the files Feature-004 changed (`retry_workflow.py`, `student_service.py`, `briefing_store.py`, `mcp_server.py`, `api.py`, `tests/test_defect_resolution.py`) | — | All checks passed |
| `uv run ruff check src/student_attrition_risk/ui.py` | 3 findings: I001 line 3 (A10), F401 `Decimal` line 6 (A8), F401 `StudentNotAtRiskError` line 20 (A9) | The same 3 findings (A9 now at line 21 because B1 added one import line); Feature-004 adds none |
| `uv run ruff check .` | 7 errors | The same 7 errors, all on lines Feature-004 did not touch |

### 1.2 Post-fix results (teammate High defects resolved; `1b5225e`, 2026-09-25)

| Check | Before (`1b5225e`'s parent, `main` after PR #114) | After (`1b5225e`) |
|---|---|---|
| `uv run pytest -q` | 236 passed, 5 failed, 13 skipped | **260 passed, 0 failed, 13 skipped** |
| `uv run pytest tests/test_defect_resolution_teammate_highs.py -q` | — (file did not exist) | 19 passed (D1 3, D2 4, D3 6, A5 2, D7 3, baseline 1) |
| `uv run pytest tests/test_ui.py -q` | 14 passed, 5 failed | 19 passed |
| `uv run ruff check .` | 7 errors | 4 errors, all on files this change did not touch (`ui.py`: A8, A9, A10; `briefing_instructions.py`: A10) |
| Mock-mode smoke (`USE_MOCK_DATA=true`, no model name) | Every route 500 | `/api/health` 200; profile 200; `POST /briefing` 503 "Briefing generation is not configured" |

Each new regression test fails against the code before `1b5225e` and passes after it.

## 2. Decisions (product owner, 2026-09-24 — final)

| # | Decision |
|---|---|
| DEC-1 | Severity scale is Critical / High / Medium / Low. US-20 is met when every Critical and High defect in scope is closed and every lower-priority defect is documented here. |
| DEC-2 | Feature-004 fixes Renny's (RennyMatis2000) own defects only. Teammates' defects are logged with owner and severity and left unfixed (constitution Principle XVI). |
| DEC-3 | Fixed in Feature-004: **B1, B2, B4, C3 (the briefing-tool half only, `mcp_server.py:34-57`; see DEC-11)**. B2 is rated High. |
| DEC-4 | Renny's defects logged only, not fixed: **C7** (Low), **A9** (Low). |
| DEC-5 | Not defects, recorded as design decisions: **C6** (`st.error` kept on error paths, deliberately red) and **DD-2** (small-group suppression commented out at `student_repository.py:367`, deliberate). |
| DEC-6 | Karen's five failing `tests/test_ui.py` tests are logged against Karen. They are not edited and not superseded. |
| DEC-7 | Done-gate for each fix: ruff clean on changed files; `uv run pytest` shows exactly the 5 known `tests/test_ui.py` failures and no others. |
| DEC-8 | Regression tests go in a new file `tests/test_defect_resolution.py` only, one test group per defect named after its register ID. Merged test files are never edited. |
| DEC-9 | Karen's `StructuredBriefingValidator` is already wired in `main.build_service` (`87670e4`), so the validation half of Feature-001 SC-007 is satisfied by her work. The instructions half (US-12) is still open. Not a Feature-004 item. |
| DEC-10 | (2026-09-24, clarification) B1's advisor-facing message is produced only inside Renny's `request_briefing()` (`ui.py:461-480`) as a red page-owned notice in the existing error palette. GuaGuaGua88's handlers (`ui.py:730-733`, `768-771`) are not changed. |
| DEC-11 | (2026-09-24, clarification) C3's Renny half covers both briefing tools, `generate_student_briefing` and `get_student_briefing` (`mcp_server.py:34-57`). Lines 21-33 are not changed. |
| DEC-13 | (2026-09-25) Karen and GuaGuaGua88 approved resolving their six High defects (D1, D2, D3, A1–A4/C1, A5, D7). This supersedes DEC-2 and DEC-6 for those items only. `tests/test_ui.py` is corrected in place with the owner's approval; the other regression tests go in a new file, `tests/test_defect_resolution_teammate_highs.py`. Fixed in `1b5225e`. |
| DEC-12 | (2026-09-24, clarification) C3 read-outage re-raised as BriefingStorageError with safe text to preserve the Feature-003 boundary test. `get_student_briefing` maps a `BriefingStorageError` to a fresh `BriefingStorageError("validated briefing store unavailable") from None`; any other unexpected failure in either briefing tool becomes a `ToolError` with the REST-matching safe message. |

## 3. Register

Action values: **Fix in Feature-004** · **Logged to owner** · **Not a defect – design decision** · **Unverified**.

### 3.1 Renny (RennyMatis2000)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| B1 (= C2, A7) | `student_service.py:122` → `api.py:64-67`; `ui.py:467` (also `ui.py:768-771`) | A store **read** outage during `POST /briefing` (non-regenerate) or during the UI Regenerate pre-check is reported as "Validated briefing could not be stored" / "generated but could not be stored", although nothing was generated or written. | 002 Edge Cases (read-time unreachable → explicit error); 002 FR-036 / FR-038 (misleading outcome) | Medium | Renny | Fix in Feature-004 | Closed (tests/test_defect_resolution.py — section B1; fix `c7f80b2`, merge `27c5db0`; see § 5) |
| B2 | `retry_workflow.py:98` (also `student_service.py:150`) | An exception raised by the validator on Attempt 2 escapes `SingleRetryWorkflow.run`: no terminal outcome is logged and the API answers "Databricks data source unavailable". Real trigger: D4 (NaN score). | 002 FR-005, SC-002 | High | Renny | Fix in Feature-004 | Closed (tests/test_defect_resolution.py — section B2; fix `3778a58`, merge `46c65ed`; see § 5) |
| B4 | `briefing_store.py:64-66`, `84-89` | Any non-briefing file in a student's Volume folder makes `has_validated` true and becomes the "latest" briefing, so every retrieval for that student fails until the file is deleted by hand. | 002 FR-022 / FR-023, SC-008 | Medium | Renny | Fix in Feature-004 | Closed (tests/test_defect_resolution.py — section B4; fix `2824837`, merge `0fa503d`; see § 5) |
| C3 (Renny half) | `mcp_server.py:34-57` (sweep cited 49-58; DEC-11) | The MCP briefing tools let backend exceptions through; FastMCP forwards the raw text (Volume paths, warehouse errors) to the client, while REST returns safe 503 messages. | App README ("503 with safe messages"); constitution X, XI (sweep also cited 002 FR-032, which concerns attempt-count display) | Medium | Renny | Fix in Feature-004 | Closed (tests/test_defect_resolution.py — section C3; fix `7447dd6`, merge `cf8187e`; see § 5) |
| C7 | `api.py:81-84` | `GET /briefing` says "store unavailable" when the data source is what is down (503 either way). | — | Low | Renny | Logged to owner | Open |
| A9 | `ui.py:20` | Unused import `StudentNotAtRiskError` (F401). | — | Low | Renny | Logged to owner | Open |

### 3.2 Karen (karen-lee1029 / k224.lee)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| D1 | `briefing_validation.py:54` | Risk-level check is a substring match on "at risk", so "Not At Risk" passes. | US-14 | High | Karen | Fixed with owner approval (DEC-13) | Closed (`1b5225e`; see § 5.1) |
| D2 | `briefing_validation.py:67` | Score check accepts the integer part anywhere in the text ("78" for 78.5%). | US-14 | High | Karen | Fixed with owner approval (DEC-13) | Closed (`1b5225e`; see § 5.1) |
| D3 | `briefing_validation.py:211` | "Mentions student data" check effectively always passes (0/1 values match any digit). | US-14 | High | Karen | Fixed with owner approval (DEC-13) | Closed (`1b5225e`; see § 5.1) |
| D4 | `briefing_validation.py:211` | NaN raises `ValueError`, inf raises `OverflowError`; triggers B2 on Attempt 2. | US-14 | Medium | Karen | Closed incidentally by the D3 fix | Closed (`1b5225e`; `test_d3_non_finite_values_are_skipped_rather_than_crashing`) |
| D5 | `briefing_validation.py:148`, `165` | AC5 is appended to the failed criteria twice. | US-14 | Low | Karen | Logged to owner | Open |
| D6 | `briefing_validation.py:109`, `111` | The "I'm going to" / "I've contacted" regexes never match. | US-14 | Medium | Karen | Logged to owner | Open |
| A1–A4 / C1 | `tests/test_ui.py:235-337` | 5 tests fail against the current UI: they expect `st.info`, an "Attempt:" label (contradicts 002 FR-032), and a `FakeService` without `has_stored_briefing`. Corrected in place with the owner's approval (DEC-13). | 002 FR-032 | High | Karen | Fixed with owner approval (DEC-13) | Closed (`1b5225e`; see § 5.1) |
| A5 | `main.py:81-84` | `ConfigurationError` is swallowed and `app=None`, so every route returns 500 with no cause shown. Joint with D7. | 001 FR-014 | High | Karen (joint with GuaGuaGua88, D7) | Fixed with owner approval (DEC-13) | Closed (`1b5225e`; see § 5.1) |
| A10 (Karen part) | `briefing_validation.py:9`, `tests/test_ui.py:13` | I001 unsorted imports. | — | Low | Karen | Fixed while editing these files (DEC-13) | Closed (`1b5225e`) |

### 3.3 GuaGuaGua88 (l52.yang)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| D7 (= A6, B5, C5) | `main.py:29-32` | Mock mode requires `DATABRICKS_MODEL_NAME`, so the README quick start fails and the whole app is unusable. | 001 FR-014 | High | GuaGuaGua88 | Fixed with owner approval (DEC-13) | Closed (`1b5225e`; see § 5.1) |
| D8 | `config.py:87-88` | A blank or non-numeric port raises an uncaught `ValueError` at import. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| D9 | `config.py:78` | `USE_MOCK_DATA` values "1" / "yes" / " true" are read as false, so the app silently runs live. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| D10 | `databricks_client.py:16-21` | Token set with host unset raises `AttributeError`. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| C3 (other half) | `mcp_server.py:21-33` | Profile and list MCP tools leak raw exception text. | App README; 001 | Medium | GuaGuaGua88 | Logged to owner | Open |
| C4 | `mcp_server.py:21-28` | REST and MCP disagree for an unknown student and for `limit=0`. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| C8 | `ui.py:793-856` | Opening and closing `div` wrappers are emitted in separate `st.markdown` calls, so they never wrap the content. | — | Low | GuaGuaGua88 | Logged to owner | Open |
| A8, A10 (part) | `ui.py:6`; `ui.py`, `main.py`, `briefing_instructions.py` | F401 unused `Decimal`; I001 import order. The `main.py` import order was fixed in `1b5225e` while resolving D7; `ui.py` and `briefing_instructions.py` remain. | — | Low | GuaGuaGua88 | Logged to owner | Open (partly fixed) |

### 3.4 Third party

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| A11 | — (test run warnings) | Starlette / Authlib deprecation warnings. | — | Low | Third party | Logged to owner | Open |

### 3.5 Design decisions (not defects)

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| C6 | `ui.py` (error paths) | `st.error` is used on error paths. Kept red deliberately. | — | — | Renny | Not a defect – design decision | Open |
| DD-2 | `student_repository.py:367` | Small-group suppression is commented out deliberately. | — | — | GuaGuaGua88 | Not a defect – design decision | Open |

### 3.6 Suspected, unconfirmed

Recorded so they are not lost; none is treated as a defect until reproduced.

| ID | File:line | Description | Spec reference | Severity | Owner | Action | Status |
|---|---|---|---|---|---|---|---|
| U1 | — | In-memory store is not shared between the Streamlit process and REST/MCP when `BRIEFING_VOLUME` is unset (local only). | — | — | — | Unverified | Open |
| U2 | — | Volume store uses the raw hash in its path. Not exploitable: entry points check the hash exists. | — | — | — | Unverified | Open |
| U3 | — | `LIMIT ?` placeholder on Databricks. | — | — | — | Unverified | Open |
| U4 | — | Case-sensitive column lookup. | — | — | — | Unverified | Open |
| U5 | — | `Decimal` / date types from live Databricks versus the validator. | — | — | — | Unverified | Open |
| U6 | — | AC7 8–10 digit false positive. | — | — | — | Unverified | Open |
| U7 | — | Proxy header merge. | — | — | — | Unverified | Open |
| U8 | — | WebSocket close codes. | — | — | — | Unverified | Open |

## 4. Summary by severity

| Severity | Total | Fix in Feature-004 | Logged to owner |
|---|---|---|---|
| Critical | 0 | 0 | 0 |
| High | 7 | 1 (B2) — Closed | 6 (D1, D2, D3, A1–A4/C1, A5, D7) — **Closed** with owner approval (DEC-13) |
| Medium | 6 | 3 (B1, B4, C3 Renny half) — Closed | 3: D4 Closed (by the D3 fix); D6, C3 other half — Open |
| Low | 11 | 0 | 11 (incl. Renny's C7, A9) — Open |

Design decisions (C6, DD-2) and unverified items (U1–U8) carry no severity and are not counted.

US-20 status against DEC-1: **met project-wide.** No Critical defect was found, and all seven High
defects are closed: B2 by Feature-004, and the six teammate-owned Highs (Karen: D1, D2, D3, A1–A4/C1,
A5; GuaGuaGua88: D7) in `1b5225e` with their owners' approval (DEC-13). Every remaining lower-priority
defect is documented in § 6.

## 5. Closure evidence

Each closed entry's regression group is in `student_attrition_risk_app/tests/test_defect_resolution.py`
and passes at `27c5db0`. Merge commits are local to `feat/feature-004-final-defect-resolution`.

| ID | Fix commit | Merge commit | Regression tests |
|---|---|---|---|
| B2 (High) | `3778a58` | `46c65ed` | 6 tests: `test_b2_attempt2_validator_exception_is_terminal_validation_failure`, `test_b2_attempt2_validator_exception_is_reported_as_briefing_failure_over_rest`, `test_b2_attempt2_validator_exception_logs_one_metadata_only_terminal_outcome`, `test_b2_attempt1_validator_exception_proceeds_to_retry_with_original_prompt`, `test_b2_validator_configuration_error_is_surfaced_unchanged` (parametrised: attempt 1, attempt 2) |
| C3, Renny half (Medium) | `7447dd6` | `cf8187e` | 9 tests: `test_c3_get_student_briefing_store_read_failure_is_safe`, `test_c3_get_student_briefing_other_failure_is_safe`, `test_c3_mcp_client_receives_only_the_safe_message` (parametrised: both tools), `test_c3_generate_student_briefing_data_source_failure_is_safe`, `test_c3_safely_mapped_failures_are_unchanged` (parametrised: 3 cases), `test_c3_configuration_failure_keeps_its_own_text` |
| B4 (Medium) | `2824837` | `0fa503d` | 4 tests: `test_b4_folder_with_only_an_unrelated_file_has_no_briefing`, `test_b4_unrelated_file_sorting_last_does_not_hide_the_stored_briefing`, `test_b4_save_after_a_stray_file_becomes_latest_and_leaves_the_file_untouched`, `test_b4_unrelated_files_are_ignored_without_logging` |
| B1 = C2, A7 (Medium) | `c7f80b2` | `27c5db0` | 8 tests: `test_b1_store_read_failure_raises_store_unavailable_without_generating` (parametrised: `regenerate` False / True), `test_b1_store_read_failure_logs_one_store_unavailable_outcome`, `test_b1_rest_post_briefing_store_read_failure_is_store_unavailable`, `test_b1_generate_tool_store_read_failure_is_store_unavailable`, `test_b1_write_failure_is_still_could_not_be_stored`, `test_b1_ui_store_read_failure_shows_red_store_unavailable_notice` (parametrised: Generate and Regenerate) |

C2 and A7 are sweep duplicates of B1 and close with it. For A7 this covers Renny's
`request_briefing()` (DEC-10); GuaGuaGua88's handlers at `ui.py:730-733` and `768-771` were not changed.

### 5.1 Teammate-owned High defects (DEC-13)

Regression groups are in `student_attrition_risk_app/tests/test_defect_resolution_teammate_highs.py`, except A1–A4/C1, which are closed by
the corrected `tests/test_ui.py` itself. All pass at `1b5225e`.

| ID | Fix | Regression tests |
|---|---|---|
| D1 (High) | Risk level must match the prediction; the negated "not at risk" form is checked separately | `test_d1_not_at_risk_briefing_fails_for_a_flagged_student`, `test_d1_hyphenated_at_risk_is_accepted_for_a_flagged_student`, `test_d1_not_at_risk_is_required_for_a_student_who_is_not_flagged` |
| D2 (High) | Score accepted only as supplied, to one decimal place with `%` | `test_d2_wrong_score_with_an_unrelated_78_fails`, `test_d2_score_without_its_decimal_place_fails`, `test_d2_score_inside_a_larger_number_fails`, `test_d2_score_with_a_space_before_the_percent_sign_passes` |
| D3 (High), D4 (Medium) | Whole-number and whole-phrase matching; 0/1, boolean and non-finite values skipped | `test_d3_generic_context_fails_traceability`, `test_d3_digits_inside_other_numbers_do_not_count_as_a_mention`, `test_d3_zero_and_one_values_do_not_count_as_a_mention`, `test_d3_common_words_from_text_values_do_not_count_as_a_mention`, `test_d3_a_whole_text_value_counts_as_a_mention`, `test_d3_non_finite_values_are_skipped_rather_than_crashing` |
| A5 (High) | Invalid configuration yields a stand-in app that answers 503 naming the problem, and logs it | `test_a5_configuration_error_app_names_the_problem_with_503`, `test_a5_configuration_error_is_logged` |
| D7 (High) | No model name → `StubGenerationProvider`, which fails only when a briefing is requested (001 FR-014) | `test_d7_mock_mode_builds_without_a_model_name` (parametrised: unset, blank), `test_d7_briefing_request_without_a_model_name_fails_only_at_request_time` |
| A1–A4 / C1 (High) | Assertions updated to the current UI: page-owned notices, no attempt label (002 FR-032), `has_stored_briefing` on `FakeService` | The five previously failing `tests/test_ui.py` tests now pass |

## 6. Known limitations and open items at delivery

**US-20 is complete.** Every Critical and High defect is closed: B1, B2, B4 and C3 (Renny half) by
Feature-004, and D1, D2, D3, A1–A4/C1, A5 and D7 with their owners' approval (DEC-13). The
lower-priority defects that remain are documented below, as the US-20 acceptance criterion requires.

### 6.1 Open defects by owner

| Owner | High | Medium | Low |
|---|---|---|---|
| Karen (karen-lee1029 / k224.lee) | — | D6 | D5 |
| GuaGuaGua88 (l52.yang) | — | C3 (other half, `mcp_server.py:21-33`) | D8, D9, D10, C4, C8, A8, A10 (`ui.py`, `briefing_instructions.py`) |
| Renny (RennyMatis2000) | — | — | C7, A9 (logged only, DEC-4) |
| Third party | — | — | A11 |

Design decisions C6 and DD-2 stand as recorded in § 3.5. Unverified items U1–U8 (§ 3.6) remain
unconfirmed and are not counted as defects.

### 6.2 Other limitations

- **Test failures**: none. `uv run pytest -q` shows 260 passed, 0 failed, 13 skipped at `1b5225e`.
- **Pre-existing lint**: `uv run ruff check .` reports 4 findings, all autofixable and on files not
  touched by the fixes: A8 (F401 `Decimal`), A9 (F401 `StudentNotAtRiskError`) and A10 (I001) in
  `ui.py`, and A10 (I001) in `briefing_instructions.py`.
- **Feature-001 SC-007**: the validation half is satisfied by Karen's `StructuredBriefingValidator`
  wiring in `main.build_service` (`87670e4`). The instructions half (US-12) is still open and is
  not a Feature-004 item (DEC-9).
- **Test skips**: 13 tests in `tests/test_dashboard.py` skip without a live Databricks workspace;
  unchanged from the baseline.
