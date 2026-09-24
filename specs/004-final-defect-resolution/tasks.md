# Tasks: Feature-004 — Final Defect Resolution (US-20)

**Input**: Design documents from `specs/004-final-defect-resolution/`
**Prerequisites**: [plan.md](./plan.md) (change map), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/failure-messages.md](./contracts/failure-messages.md), [quickstart.md](./quickstart.md), [defect-register.md](./defect-register.md)

**Tests**: Required. The spec (FR-023, FR-024) requires one regression group per fixed defect, in
the single new file `student_attrition_risk_app/tests/test_defect_resolution.py`, named after the
register ID. Write each group first and confirm it fails before the fix.

**Organisation**: One phase per defect so the defects run as parallel tracks. Story labels map to
spec.md: **US1 = B2**, **US2 = B1**, **US3 = B4**, **US4 = C3**, **US5 = register**.

All paths below are relative to `student_attrition_risk_app/` unless they start with `specs/`.
Line numbers are as of `3181882` (see plan.md § Change map). Only the listed lines may change; never
edit a merged test file or a teammate's lines.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)

---

## Phase 1: Setup

- [X] T001 Create the regression skeleton `tests/test_defect_resolution.py`: module docstring naming Feature-004 / US-20 and `specs/004-final-defect-resolution/defect-register.md`, then four delimited sections in order B2, B4, C3, B1; imports cleanly and collects 0 tests; ruff clean.

**Checkpoint**: `uv run pytest tests/test_defect_resolution.py` collects 0 tests; the full suite still reads 209 passed / 5 failed (`tests/test_ui.py`) / 13 skipped.

No foundational phase: the tracks share no prerequisite beyond T001.

---

## Phase 2: Track B2 — the retry workflow always ends with an explicit outcome (US1, P1, High) 🎯 MVP

**Goal**: A validator exception never escapes the workflow (spec FR-007–FR-011).

**Independent test**: section `B2` of `tests/test_defect_resolution.py` passes; no other file's result changes.

- [X] T002 [US1] In the `B2` section of `tests/test_defect_resolution.py`, add a local `RaisingValidator` double (validator whose `validate` raises a scripted exception per call, falling back to scripted `ValidationOutcome`s) and tests: (a) Attempt-1 validation fails, Attempt-2 validator raises `ValueError` → service raises `BriefingNotProducedError` with `category == "validation"`, nothing stored; (b) same case via `build_rest_client` → 502 `Briefing could not be produced (validation)`, never "Databricks data source unavailable"; (c) same case, `caplog` shows exactly one `terminal_validation` workflow line, metadata only; (d) Attempt-1 validator raises, Attempt-2 passes → validated briefing with `attempt_count == 2` stored once and the retry prompt equals the original (no feedback block); (e) validator raises `ConfigurationError` on either attempt → surfaced unchanged. Confirm (a)–(d) fail before T003/T004.
- [X] T003 [US1] In `src/student_attrition_risk/retry_workflow.py` lines 98-100, wrap `self.validator.validate(draft, retry_context)`: re-raise `ConfigurationError`; any other exception → `return TerminalFailure(category="validation")`. Update the class docstring line 76-77 only if it no longer holds.
- [X] T004 [US1] In `src/student_attrition_risk/student_service.py` lines 150-163, wrap the Attempt-1 `self.validator.validate(draft, context)`: re-raise `ConfigurationError`; any other exception → `self._hand_off_to_retry(student_hash, context, ValidationFailed(outcome=ValidationOutcome(passed=False, validator_id=getattr(self.validator, "validator_id", "unavailable"))))` (research R1).
- [X] T005 [US1] Done-gate B2: `uv run ruff check src/student_attrition_risk/retry_workflow.py src/student_attrition_risk/student_service.py tests/test_defect_resolution.py` clean; `uv run pytest -q` shows only the 5 known `tests/test_ui.py` failures.

**Checkpoint**: B2 closed-ready. Unblocks B1 (shares `student_service.py`).

---

## Phase 3: Track B4 — unrelated files never hide a student's briefing (US3, P3) — independent

**Goal**: The Volume store only counts files it wrote itself (spec FR-016–FR-018).

**Independent test**: section `B4` passes.

- [X] T006 [P] [US3] In the `B4` section of `tests/test_defect_resolution.py`, using `volume_store()` / `FakeFilesClient` from `workflow_doubles`: (a) student folder holding only `notes.txt` → `has_validated` is `False` and `get_latest_validated` is `None`; (b) a stored briefing plus `zzz-readme.json` (sorts last) → latest returns the stored briefing; (c) with a stray file present, `save_validated` makes the new briefing the latest and the stray file is still in `fake.files` unchanged; (d) no log record is emitted for the stray file (`caplog`). Confirm (a)–(c) fail before T007.
- [X] T007 [US3] In `src/student_attrition_risk/briefing_store.py`: add `import re` (lines 8-10) and a module constant `_BRIEFING_NAME = re.compile(r"^\d{8}T\d{12}Z-attempt\d+-[0-9a-f]{6}\.json$")` after the imports (line 16); in `has_validated` (lines 64-66) and `get_latest_validated` (lines 84-86) count an entry only if it is not a directory **and** `_BRIEFING_NAME.match(entry.path.rsplit("/", 1)[-1])`. Leave `save_validated` (101-118) and `_file_path` unchanged. No logging.
- [X] T008 [US3] Done-gate B4: ruff clean on `src/student_attrition_risk/briefing_store.py` and the test file; full suite shows only the 5 known failures.

---

## Phase 4: Track C3 — briefing tools never leak internal error text (US4, P4)

**Goal**: Both briefing tools return the REST-equivalent safe message (spec FR-019–FR-022, contract).

**Independent test**: section `C3` passes.

- [X] T009 [P] [US4] In the `C3` section of `tests/test_defect_resolution.py`, via `build_mcp_server` and the FastMCP in-process client (as `tests/test_mcp_tools.py` does, without editing it): (a) `get_student_briefing` with a store whose read raises `BriefingStorageError("could not list stored briefings for /Volumes/secret/path")` → `ToolError` text is `validated briefing store unavailable` and contains no `/Volumes`; (b) `generate_student_briefing` whose generation path raises `RuntimeError("warehouse xyz exploded")` outside the workflow (e.g. repository `get_model_features` raising) → `databricks data source unavailable`, no `warehouse`; (c) not found / not at risk / configuration messages unchanged. Confirm (a)–(b) fail before T010. *(DEC-12: (a) instead expects `BriefingStorageError("validated briefing store unavailable")` with the cause suppressed.)*
- [X] T010 [US4] In `src/student_attrition_risk/mcp_server.py`: in `generate_student_briefing` (lines 35-47) add a final `except Exception` → `ToolError("databricks data source unavailable")`; in `get_student_briefing` (lines 50-54) add `except Exception` after `StudentNotFoundError` → `ToolError("validated briefing store unavailable")`. Do not touch lines 21-33. *(DEC-12: a `BriefingStorageError` is first re-raised as `BriefingStorageError("validated briefing store unavailable") from None`.)*
- [X] T011 [US4] Done-gate C3: ruff clean on `src/student_attrition_risk/mcp_server.py` and the test file; full suite shows only the 5 known failures.

**Checkpoint**: C3 closed-ready. Unblocks B1 (shares `mcp_server.py`).

---

## Phase 5: Track B1 — a storage read outage is reported as what it is (US2, P2) — after B2 and C3

**Goal**: A store read failure is "store unavailable" at every boundary (spec FR-012–FR-015, contract).

**Independent test**: section `B1` passes.

- [X] T012 [US2] In the `B1` section of `tests/test_defect_resolution.py`, with a local store double whose `has_validated` / `get_latest_validated` raise `BriefingStorageError` and whose `save_validated` records calls: (a) `service.request_briefing(h)` raises `BriefingStoreUnavailableError`, generation not called, nothing saved; (b) REST `POST /briefing` → 503 `Validated briefing store unavailable`; (c) tool `generate_student_briefing` → `validated briefing store unavailable`; (d) write failure (store whose only failing call is `save_validated`) still → 503 `Validated briefing could not be stored`; (e) Streamlit `AppTest` on `src/student_attrition_risk/ui.py` with the service patched as in `tests/test_ui.py`: Generate and Regenerate each render a `.store-error-notice` containing "Store unavailable", no element contains "could not be stored", and `at.error` is empty. Confirm (a)–(c), (e) fail before T013–T016.
- [X] T013 [US2] In `src/student_attrition_risk/student_service.py`: add `class BriefingStoreUnavailableError(BriefingStorageError)` after line 54; wrap lines 122-123 (`has_validated` / `get_latest_validated` on the request path) and line 192 (`has_stored_briefing`) so a `BriefingStorageError` is re-raised as `BriefingStoreUnavailableError` (`from exc`), logged once via `_log_outcome(outcome="store_unavailable", exception=exc)`. `_persist` unchanged.
- [X] T014 [P] [US2] In `src/student_attrition_risk/api.py`: import `BriefingStoreUnavailableError` (lines 7-13) and, in `request_briefing` before the `BriefingStorageError` handler (line 64), map it to 503 `Validated briefing store unavailable`.
- [X] T015 [P] [US2] In `src/student_attrition_risk/mcp_server.py`: import `BriefingStoreUnavailableError` (lines 6-12) and, in `generate_student_briefing` before the `BriefingStorageError` handler (line 44), map it to `ToolError("validated briefing store unavailable")`.
- [X] T016 [P] [US2] In `src/student_attrition_risk/ui.py`: (1) import `BriefingStoreUnavailableError` on its own line in the `student_service` import (lines 17-22; leave line 19 as is); (2) add `.store-error-notice` after `.page-notice` (lines 333-343) with `background: #fee4e2; border: 1px solid #d92d20; border-left: 4px solid #d92d20; color: #b42318;` and the same radius/padding/margin/font as `.page-notice`; (3) at line 441 make `style` positional-or-keyword in `render_notice` (drop the `*`), so line 789 `render_notice(*message)` accepts a 3-tuple; (4) in `request_briefing` (lines 461-480) wrap lines 467 and 469 in `try/except BriefingStoreUnavailableError`: pop `ui_success`, set `st.session_state.ui_message = ("Store unavailable", "Validated briefing store unavailable.", "store-error-notice")`, and `return`. No `st.error`/`st.info`/`st.warning`. Do not touch lines 725-737, 763-775, 787-788.
- [X] T017 [US2] Done-gate B1: ruff clean on `student_service.py`, `api.py`, `mcp_server.py`, the test file; `uv run ruff check src/student_attrition_risk/ui.py` shows no finding beyond those at `3181882` (A8, A9, A10); full suite shows only the 5 known failures.

---

## Phase 6: Register and close-out (US5, P5)

- [X] T018 [US5] In `specs/004-final-defect-resolution/defect-register.md`: set B2, B4, C3 (Renny half) and B1 to `Closed (tests/test_defect_resolution.py — section <ID>)`; add a "Post-fix results" row to § 1 with the new pytest/ruff counts; confirm § 4 still lists the six open High defects with owners and states that Feature-004 completes US-20 for Renny's scope only (spec FR-031, FR-032).
- [X] T019 Run `specs/004-final-defect-resolution/quickstart.md` §§ 1-2 and record the final counts in the PR description.

---

## Dependencies & execution order

```text
T001 ──┬── Track B2  (T002→T003,T004→T005) ──┐
       ├── Track B4  (T006→T007→T008)        │  (independent; can finish any time)
       └── Track C3  (T009→T010→T011) ───────┤
                                             └── Track B1 (T012→T013→T014,T015,T016→T017)
                                                            └── T018 → T019
```

- **B1 depends on B2 and C3**: B1 edits `student_service.py` (shared with B2: B2 at 150-163, B1 at 53-54, 122-123, 186-192) and `mcp_server.py` (shared with C3: C3 at 34-57, B1 at 6-12 and 42-45).
- **B4 is independent**: only `briefing_store.py` and its own test section.
- All tracks append to different sections of the same test file; merge section by section.
- T018 needs all four done-gates (T005, T008, T011, T017).

## Parallel opportunities

- After T001: tracks B2, B4 and C3 run in parallel (different source files).
- Within B1, after T013: T014 (`api.py`), T015 (`mcp_server.py`) and T016 (`ui.py`) run in parallel.

## Implementation strategy

1. **MVP = Track B2** (the only High defect in scope; meets US-20's criterion for Renny's scope on its own).
2. Add B4 and C3 in parallel, then B1.
3. Close the register (T018) and run the done-gate (T019). No push or merge without the product owner.
